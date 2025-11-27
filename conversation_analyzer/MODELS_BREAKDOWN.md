# Hugging Face Models Breakdown - Current Usage & Potential

## Currently Active Models (Throttled for Performance)

### 1. **Emotion Classification**
**Model:** `j-hartmann/emotion-english-distilroberta-base` (emotion_distilroberta)
- **What it does:** Classifies text into 7 emotions: joy, sadness, anger, fear, surprise, disgust, neutral
- **Current output:** Emotion scores per turn (e.g., "neutral: 0.89")
- **What we're getting:** ✅ Top emotions aggregated across conversation
- **What we're missing:**
  - Emotion transitions (how emotions change over time)
  - Emotion intensity trends
  - Specific phrases that trigger each emotion
  - Emotion co-occurrence patterns

**Available but NOT used:**
- `bhadresh-savani/distilbert-base-uncased-emotion` - Different emotion taxonomy, could provide validation
- `cardiffnlp/twitter-roberta-base-emotion` - Better for conversational/social media style

---

### 2. **Stress Detection**
**Model:** `finiteautomata/beto-emotion-analysis` (beto_emotion)
- **What it does:** Detects stress/negative sentiment in Spanish/English text
- **Current output:** Stress scores per turn
- **What we're getting:** ✅ Average stress, peak stress, detection count
- **What we're missing:**
  - Stress triggers (which words/phrases cause stress spikes)
  - Stress patterns over time (when stress builds up)
  - Stress recovery patterns
  - Correlation with specific topics

**Available but NOT used:**
- `Hate-speech-CNERG/bert-base-uncased-hatexplain` - Detects aggression/negativity, could identify hostile language patterns

---

### 3. **Psychological Labels (Zero-Shot)**
**Model:** `valhalla/distilbart-mnli-12-1` (zero_shot_psych)
- **What it does:** Zero-shot classification into custom psychological categories
- **Current labels:** avoidance, self-criticism, reflection, decisiveness, support-seeking, stress
- **Current output:** Scores for each label per turn, pattern counts
- **What we're getting:** ✅ Which patterns appear (e.g., "avoidance: 67 turns")
- **What we're missing:**
  - **WHICH SPECIFIC TEXTS show avoidance** (this is what you asked for!)
  - Confidence scores for each detection
  - Pattern intensity (not just presence/absence)
  - Pattern sequences (avoidance → stress → self-criticism)
  - Custom labels for specific use cases

---

### 4. **Named Entity Recognition (NER)**
**Model:** `dslim/bert-base-NER` (ner_triggers)
- **What it does:** Extracts named entities: PERSON, ORGANIZATION, LOCATION, MISC
- **Current output:** List of unique entities (people, places, topics)
- **What we're getting:** ✅ Key entities mentioned
- **What we're missing:**
  - Entity frequency (how often each is mentioned)
  - Entity-emotion correlation (emotions when discussing specific people/topics)
  - Entity-timeline (when entities appear in conversation)
  - Entity relationships (who talks about what)
  - Custom entity types (triggers, topics, concerns)

---

### 5. **Embeddings**
**Model:** `sentence-transformers/all-MiniLM-L6-v2` (minilm)
- **What it does:** Converts text to 384-dimensional vectors for semantic similarity
- **Current output:** Vector embeddings stored in database
- **What we're getting:** ✅ Stored for future use
- **What we're missing:**
  - **Semantic clustering** (grouping similar turns together)
  - **Topic modeling** (finding recurring themes automatically)
  - **Similarity search** (finding similar past conversations)
  - **Pattern detection** (finding recurring phrases/patterns)
  - **Long-term memory** (connecting current conversation to past ones)

**Available but NOT used:**
- `sentence-transformers/all-mpnet-base-v2` - Better quality embeddings (768-dim)
- `hkunlp/instructor-xl` - Instruction-tuned embeddings, better for specific tasks

---

## Models Available but NOT Currently Used

### 6. **Summarization Models**
**Models:** `facebook/bart-large-cnn`, `t5-base`
- **What they could do:** Generate concise summaries of conversation segments
- **Potential value:**
  - Summarize long conversations into key points
  - Extract main themes per speaker
  - Create timeline summaries
  - Identify key decision points

---

## What We're Missing / Could Add

### A. **Granular Text Attribution** (Your Request)
**Problem:** We know "avoidance: 67 turns" but not WHICH turns or WHICH words
**Solution approaches:**
1. **Token-level analysis:** Run models on individual sentences/phrases, not just full turns
2. **Attention visualization:** Some models can show which words contribute to predictions
3. **Highlighting:** Mark specific phrases that triggered high scores
4. **Quote extraction:** Extract and display the actual text that shows each pattern

**Example output:**
```
Avoidance Detected (67 instances):
- "I think we can do flight reimbursements I'll have to ask more about that" (score: 0.82)
- "If if if the visa is okay, then then we'll we'll figure it" (score: 0.91)
- "Mhmm" (score: 0.45)
```

### B. **Temporal Patterns**
- Emotion transitions over time
- Stress buildup patterns
- Pattern sequences (avoidance → stress → self-criticism)
- Recovery patterns

### C. **Cross-Model Insights**
- Emotion + Stress correlation
- Entity + Emotion correlation (emotions when discussing specific topics)
- Pattern co-occurrence (avoidance + self-criticism together)

### D. **Advanced Embedding Usage**
- Topic modeling (BERTopic) to find themes automatically
- Semantic search to find similar past conversations
- Clustering to group similar turns
- Long-term pattern tracking across sessions

### E. **Custom Labels**
- Add domain-specific labels (e.g., "work_stress", "relationship_concern")
- Fine-tune zero-shot model on your data
- Create user-specific labels

---

## Current Limitations

1. **Only using 1 of 3 emotion models** - Missing validation/consensus
2. **Only using 1 of 2 stress models** - Missing aggression detection
3. **Only using 1 of 3 embedding models** - Missing better quality embeddings
4. **Not using summarization models** - Missing automatic theme extraction
5. **Turn-level only** - Not analyzing sentence/phrase level for granularity
6. **No text attribution** - Can't show which specific words show patterns
7. **No temporal analysis** - Missing pattern sequences and transitions
8. **No cross-model correlation** - Missing insights from combining models

---

## Recommendations for Deeper Insights

### Immediate (Easy Wins):
1. **Add text attribution:** Show which specific turns show each pattern
2. **Use all emotion models:** Get consensus/validation
3. **Sentence-level analysis:** Break turns into sentences for granularity
4. **Pattern highlighting:** Mark specific phrases that triggered high scores

### Medium-term:
1. **Temporal analysis:** Show how patterns evolve over time
2. **Cross-model correlation:** Combine emotion + stress + patterns
3. **Topic modeling:** Use embeddings to find themes automatically
4. **Custom labels:** Add domain-specific psychological patterns

### Long-term:
1. **Fine-tuning:** Train models on your specific use case
2. **Multi-session analysis:** Track patterns across multiple conversations
3. **Personalization:** Learn individual user patterns
4. **Predictive insights:** Predict stress/avoidance before it happens

