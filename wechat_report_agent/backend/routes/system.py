"""System-related routes and helpers for backend migration.

This module provides a Flask Blueprint (`system_bp`) for future registration
and a `get_menu()` function that returns the menu envelope. The original
monolithic module will delegate to `get_menu()` to keep behavior identical
while allowing incremental refactoring.
"""
from flask import Blueprint, jsonify
import re

system_bp = Blueprint('system', __name__)


def _pascalize(name: str) -> str:
    parts = [p for p in name.split('-') if p]
    return ''.join(p.capitalize() for p in parts)


def normalize_icon_string(icon_val):
    if not isinstance(icon_val, str):
        return icon_val
    s = icon_val.strip()
    if s.startswith('el-icon-'):
        core = s[len('el-icon-'):]
        return 'ElIcon' + _pascalize(core)
    if s.startswith('sc-icon-'):
        core = s[len('sc-icon-'):]
        return 'ScIcon' + _pascalize(core)
    return s


def get_menu():
    # Build the same menu structure as the original implementation
    menu_array = [
        {
            'name': 'dashboard',
            'path': '/dashboard',
            'component': 'dashboard/index',
            'meta': {
                'icon': 'ElIconDataAnalysis',
                'title': '首页'
            },
            'children': [
                {
                    'name': 'collect_task_content',
                    'path': '/dashboard/collect-task-content',
                    'component': 'dashboard/collect-task-content',
                    'meta': {
                        'title': '采集内容',
                        'icon': 'ElIconNotebook'
                    }
                },
                {
                    'name': 'prompt_word_setting',
                    'path': '/dashboard/prompt-word-setting',
                    'component': 'dashboard/prompt-word-setting',
                    'meta': {
                        'title': '提示词管理',
                        'icon': 'ElIconManagement'
                    }
                },
                {
                    'name': 'report_generation',
                    'path': '/dashboard/report-generation',
                    'component': 'dashboard/report-generation',
                    'meta': {
                        'title': '报告生成',
                        'icon': 'ElIconEdit'
                    }
                },
                {
                    'name': 'generated_report',
                    'path': '/dashboard/generated-report',
                    'component': 'dashboard/generated-report',
                    'meta': {
                        'title': '已生成报告',
                        'icon': 'ElIconDocument'
                    }
                },
                {
                    'name': 'automatic_release_settings',
                    'path': '/dashboard/automatic-release-settings',
                    'component': 'dashboard/automatic-release-settings',
                    'meta': {
                        'title': '自动发送设置',
                        'icon': 'ElIconCheck'
                    }
                }
            ]
        }
    ]

    def _sanitize_value(v):
        if not isinstance(v, str):
            return v
        cleaned = ''.join(ch for ch in v if ch >= ' ')
        s = ' '.join(cleaned.split())
        return s

    def sanitize_menu_strings(node):
        if isinstance(node, dict):
            for k, val in list(node.items()):
                if isinstance(val, (dict, list)):
                    sanitize_menu_strings(val)
                else:
                    if k == 'component' and isinstance(val, str):
                        node[k] = _sanitize_value(val).replace('\n', '').replace('\r', '').strip()
                    elif k == 'path' and isinstance(val, str):
                        p = _sanitize_value(val).strip()
                        if p.startswith('/scui'):
                            p = p.replace('/scui', '', 1) or '/'
                        node[k] = p
                    else:
                        node[k] = _sanitize_value(val)
        elif isinstance(node, list):
            for item in node:
                sanitize_menu_strings(item)

    def deep_clean(node):
        if isinstance(node, dict):
            for k, v in list(node.items()):
                if isinstance(v, (dict, list)):
                    deep_clean(v)
                elif isinstance(v, str):
                    s = re.sub(r'[\r\n\t]+', ' ', v)
                    s = re.sub(r'\s{2,}', ' ', s).strip()
                    if k == 'path' and s.startswith('/scui'):
                        s = s.replace('/scui', '', 1) or '/'
                    node[k] = s
        elif isinstance(node, list):
            for item in node:
                deep_clean(item)

    def normalize_menu_icons(node):
        if isinstance(node, dict):
            meta = node.get('meta')
            if isinstance(meta, dict) and 'icon' in meta:
                meta['icon'] = normalize_icon_string(meta.get('icon'))
            for v in node.values():
                if isinstance(v, (dict, list)):
                    normalize_menu_icons(v)
        elif isinstance(node, list):
            for item in node:
                normalize_menu_icons(item)

    sanitize_menu_strings(menu_array)
    deep_clean(menu_array)
    normalize_menu_icons(menu_array)

    envelope = {
        'code': 200,
        'data': {
            'menu': menu_array,
            'dashboardGrid': [],
            'permissions': ['admin:all']
        },
        'message': 'success'
    }
    return jsonify(envelope)


@system_bp.route('/system/menu/my/1.6.1', methods=['GET'])
def system_menu_route():
    return get_menu()
