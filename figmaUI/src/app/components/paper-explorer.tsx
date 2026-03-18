import { Search, FileText, ExternalLink } from "lucide-react";
import { Input } from "./ui/input";
import { ScrollArea } from "./ui/scroll-area";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";

interface Paper {
  id: string;
  title: string;
  authors: string[];
  year: number;
  venue: string;
  citationCount: number;
}

interface PaperProfile {
  title: string;
  abstract: string;
  method: string;
  experiment: string;
  conclusion: string;
  authors: string[];
  year: number;
  venue: string;
}

const mockPapers: Paper[] = [
  {
    id: "paper:12",
    title: "Attention Is All You Need",
    authors: ["Vaswani et al."],
    year: 2017,
    venue: "NeurIPS",
    citationCount: 95847,
  },
  {
    id: "paper:45",
    title: "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
    authors: ["Devlin et al."],
    year: 2018,
    venue: "NAACL",
    citationCount: 67234,
  },
  {
    id: "paper:78",
    title: "GPT-4 Technical Report",
    authors: ["OpenAI"],
    year: 2023,
    venue: "arXiv",
    citationCount: 8965,
  },
  {
    id: "paper:91",
    title: "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
    authors: ["Lewis et al."],
    year: 2020,
    venue: "NeurIPS",
    citationCount: 3421,
  },
];

const mockPaperProfile: PaperProfile = {
  title: "Attention Is All You Need",
  abstract:
    "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
  method:
    "The Transformer uses multi-head self-attention mechanisms to process input sequences in parallel. It consists of an encoder-decoder structure where both components use stacked self-attention and point-wise, fully connected layers. Positional encodings are added to the input embeddings to inject information about the relative or absolute position of tokens in the sequence.",
  experiment:
    "We evaluated the Transformer on two machine translation tasks: WMT 2014 English-to-German and English-to-French. On the English-to-German task, our model achieved 28.4 BLEU, improving over the existing best results by over 2 BLEU. Training was performed on 8 NVIDIA P100 GPUs for 12 hours.",
  conclusion:
    "In this work, we presented the Transformer, the first sequence transduction model based entirely on attention. The Transformer can be trained significantly faster than architectures based on recurrent or convolutional layers and achieves state-of-the-art results on translation tasks.",
  authors: ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit"],
  year: 2017,
  venue: "NeurIPS 2017",
};

interface PaperExplorerProps {
  selectedPaperId: string | null;
  onPaperSelect: (id: string) => void;
}

export function PaperExplorer({ selectedPaperId, onPaperSelect }: PaperExplorerProps) {
  const selectedPaper = selectedPaperId ? mockPapers.find((p) => p.id === selectedPaperId) : null;

  return (
    <div className="w-96 border-l border-gray-200 flex flex-col bg-gray-50">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Paper Explorer</h2>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-gray-400" />
          <Input
            placeholder="Search papers..."
            className="pl-9"
          />
        </div>
      </div>

      {!selectedPaperId ? (
        /* Paper List */
        <ScrollArea className="flex-1">
          <div className="p-4 space-y-3">
            {mockPapers.map((paper) => (
              <button
                key={paper.id}
                onClick={() => onPaperSelect(paper.id)}
                className="w-full text-left p-3 bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-sm transition-all"
              >
                <div className="flex items-start gap-2 mb-2">
                  <FileText className="size-4 text-blue-600 mt-0.5 flex-shrink-0" />
                  <h3 className="text-sm font-medium text-gray-900 line-clamp-2">
                    {paper.title}
                  </h3>
                </div>
                <p className="text-xs text-gray-600 mb-2">
                  {paper.authors.join(", ")} • {paper.year}
                </p>
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge variant="secondary" className="text-xs">
                    {paper.venue}
                  </Badge>
                  <span className="text-xs text-gray-500">
                    {paper.citationCount.toLocaleString()} citations
                  </span>
                </div>
              </button>
            ))}
          </div>
        </ScrollArea>
      ) : (
        /* Paper Detail View */
        <div className="flex-1 flex flex-col">
          <div className="p-4 border-b border-gray-200 bg-white">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onPaperSelect(null!)}
              className="mb-3"
            >
              ← Back to list
            </Button>
            <div className="flex items-start gap-2">
              <FileText className="size-5 text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-gray-900 mb-2">
                  {mockPaperProfile.title}
                </h3>
                <p className="text-xs text-gray-600 mb-2">
                  {mockPaperProfile.authors.join(", ")}
                </p>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary" className="text-xs">
                    {mockPaperProfile.venue}
                  </Badge>
                  <Button variant="link" size="sm" className="h-auto p-0 text-xs">
                    <ExternalLink className="size-3 mr-1" />
                    View PDF
                  </Button>
                </div>
              </div>
            </div>
          </div>

          <Tabs defaultValue="structured" className="flex-1 flex flex-col">
            <TabsList className="mx-4 mt-4">
              <TabsTrigger value="structured" className="text-xs">
                Structured
              </TabsTrigger>
              <TabsTrigger value="json" className="text-xs">
                JSON
              </TabsTrigger>
            </TabsList>

            <TabsContent value="structured" className="flex-1 mt-0">
              <ScrollArea className="h-full">
                <div className="p-4 space-y-4">
                  <Section title="Abstract" content={mockPaperProfile.abstract} />
                  <Section title="Method" content={mockPaperProfile.method} />
                  <Section title="Experiment" content={mockPaperProfile.experiment} />
                  <Section title="Conclusion" content={mockPaperProfile.conclusion} />
                </div>
              </ScrollArea>
            </TabsContent>

            <TabsContent value="json" className="flex-1 mt-0">
              <ScrollArea className="h-full">
                <div className="p-4">
                  <pre className="text-xs bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto font-mono">
                    {JSON.stringify(mockPaperProfile, null, 2)}
                  </pre>
                </div>
              </ScrollArea>
            </TabsContent>
          </Tabs>
        </div>
      )}
    </div>
  );
}

function Section({ title, content }: { title: string; content: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <h4 className="text-xs font-semibold text-blue-900 mb-2 uppercase tracking-wide">
        {title}
      </h4>
      <p className="text-sm text-gray-700 leading-relaxed">{content}</p>
    </div>
  );
}
