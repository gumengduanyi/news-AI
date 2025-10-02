def summarize_text(title: str, date: str, text: str) -> str:
    if not text:
        return ""
    try:
        from snownlp import SnowNLP
        s = SnowNLP(text)
        # snownlp.summary 返回句子列表，取前2句
        summary_sentences = s.summary(2)
        summary = "".join(summary_sentences)
        return summary
    except Exception as e:
        # 回退到原有截断逻辑
        first_400 = text.strip().replace("\n", "")[:400]
        return first_400 + "..."
