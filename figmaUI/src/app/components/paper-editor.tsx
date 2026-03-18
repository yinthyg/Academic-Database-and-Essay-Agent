import { useState, useEffect } from "react";
import { Save, Check } from "lucide-react";
import { Textarea } from "./ui/textarea";
import { Badge } from "./ui/badge";

interface PaperEditorProps {
  paperId: string;
}

const mockPaperContent = `# A Survey on Transformer Architectures in NLP

## Abstract

Transformer architectures have revolutionized natural language processing since their introduction in 2017. This survey examines the evolution of transformer-based models, from the original Transformer to modern variants like BERT, GPT, and T5.

## 1. Introduction

The field of natural language processing has undergone a paradigm shift with the introduction of the Transformer architecture [1]. Unlike previous sequential models such as RNNs and LSTMs, transformers leverage self-attention mechanisms to process input sequences in parallel.

### 1.1 Background

Traditional sequence-to-sequence models relied on recurrent architectures, which suffer from:
- Difficulty capturing long-range dependencies
- Sequential processing limitations
- Gradient vanishing/exploding problems

### 1.2 Motivation

This work aims to provide a comprehensive overview of transformer architectures and their applications in modern NLP systems.

## 2. Transformer Architecture

### 2.1 Self-Attention Mechanism

The self-attention mechanism is the core innovation of the Transformer [2]. It allows the model to weigh the importance of different parts of the input sequence when processing each token.

The attention function can be described as:

Attention(Q, K, V) = softmax(QK^T / √d_k)V

### 2.2 Multi-Head Attention

Multi-head attention allows the model to jointly attend to information from different representation subspaces [3].

## 3. Pre-trained Models

### 3.1 BERT

BERT (Bidirectional Encoder Representations from Transformers) introduced masked language modeling for pre-training bidirectional transformers.

### 3.2 GPT Family

The Generative Pre-trained Transformer series demonstrated the effectiveness of autoregressive language modeling at scale.

## 4. Experiments

(Content in progress...)

## 5. Conclusion

Transformer architectures have become the foundation of modern NLP systems, enabling breakthrough performance across diverse tasks.

## References

[1] Vaswani et al., "Attention Is All You Need", NeurIPS 2017
[2] Devlin et al., "BERT: Pre-training of Deep Bidirectional Transformers", NAACL 2018
[3] Brown et al., "Language Models are Few-Shot Learners", NeurIPS 2020
`;

export function PaperEditor({ paperId }: PaperEditorProps) {
  const [content, setContent] = useState(mockPaperContent);
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date>(new Date());
  const [wordCount, setWordCount] = useState(0);

  useEffect(() => {
    // Calculate word count
    const words = content.trim().split(/\s+/).filter(Boolean).length;
    setWordCount(words);

    // Auto-save simulation
    const timer = setTimeout(() => {
      setIsSaving(true);
      setTimeout(() => {
        setIsSaving(false);
        setLastSaved(new Date());
      }, 500);
    }, 1000);

    return () => clearTimeout(timer);
  }, [content]);

  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold text-gray-900">Paper Editor</h2>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="text-xs">
              {wordCount} words
            </Badge>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              {isSaving ? (
                <>
                  <Save className="size-3 animate-pulse" />
                  Saving...
                </>
              ) : (
                <>
                  <Check className="size-3 text-green-600" />
                  Saved {lastSaved.toLocaleTimeString()}
                </>
              )}
            </div>
          </div>
        </div>
        <p className="text-sm text-gray-500">
          Write your paper with AI-assisted citations and feedback
        </p>
      </div>

      {/* Editor */}
      <div className="flex-1 overflow-auto">
        <div className="max-w-4xl mx-auto p-8">
          <Textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="min-h-[calc(100vh-200px)] font-mono text-sm border-none focus-visible:ring-0 focus-visible:ring-offset-0 resize-none"
            placeholder="Start writing your paper..."
          />
        </div>
      </div>

      {/* Section Navigation (Optional) */}
      <div className="border-t border-gray-200 px-4 py-2 bg-gray-50">
        <div className="max-w-4xl mx-auto flex gap-2 overflow-x-auto">
          {["Abstract", "Introduction", "Method", "Experiments", "Conclusion", "References"].map(
            (section) => (
              <button
                key={section}
                className="px-3 py-1 text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded whitespace-nowrap"
              >
                {section}
              </button>
            )
          )}
        </div>
      </div>
    </div>
  );
}
