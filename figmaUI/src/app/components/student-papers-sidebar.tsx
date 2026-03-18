import { Plus, FileEdit, ArrowLeft } from "lucide-react";
import { Button } from "./ui/button";
import { ScrollArea } from "./ui/scroll-area";
import { Link } from "react-router";

interface StudentPaper {
  id: string;
  title: string;
  created: string;
  wordCount: number;
}

const mockStudentPapers: StudentPaper[] = [
  {
    id: "paper-1",
    title: "A Survey on Transformer Architectures in NLP",
    created: "2026-03-15",
    wordCount: 3842,
  },
  {
    id: "paper-2",
    title: "Exploring RAG Systems for Academic Research",
    created: "2026-03-10",
    wordCount: 2156,
  },
  {
    id: "paper-3",
    title: "Multi-modal Learning Approaches",
    created: "2026-03-05",
    wordCount: 1567,
  },
];

interface StudentPapersSidebarProps {
  activePaperId: string;
  onPaperSelect: (id: string) => void;
}

export function StudentPapersSidebar({
  activePaperId,
  onPaperSelect,
}: StudentPapersSidebarProps) {
  return (
    <div className="w-64 border-r border-gray-200 flex flex-col bg-gray-50">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <h1 className="text-lg font-semibold text-gray-900 mb-1">My Papers</h1>
        <p className="text-xs text-gray-500">Student Writing Workspace</p>
      </div>

      {/* Navigation */}
      <div className="p-3 border-b border-gray-200 bg-white">
        <Link to="/">
          <Button variant="outline" size="sm" className="w-full justify-start gap-2">
            <ArrowLeft className="size-4" />
            Research Copilot
          </Button>
        </Link>
      </div>

      {/* New Paper Button */}
      <div className="p-3">
        <Button className="w-full justify-start gap-2" variant="default">
          <Plus className="size-4" />
          New Paper
        </Button>
      </div>

      {/* Papers List */}
      <ScrollArea className="flex-1">
        <div className="p-3 space-y-2">
          {mockStudentPapers.map((paper) => (
            <button
              key={paper.id}
              onClick={() => onPaperSelect(paper.id)}
              className={`w-full text-left p-3 rounded-lg border transition-all ${
                activePaperId === paper.id
                  ? "bg-white border-blue-200 shadow-sm"
                  : "bg-white border-gray-200 hover:border-gray-300 hover:shadow-sm"
              }`}
            >
              <div className="flex items-start gap-2 mb-2">
                <FileEdit className="size-4 text-blue-600 mt-0.5 flex-shrink-0" />
                <h3 className="text-sm font-medium text-gray-900 line-clamp-2">
                  {paper.title}
                </h3>
              </div>
              <div className="flex items-center justify-between text-xs text-gray-500 mt-2">
                <span>{paper.wordCount} words</span>
                <span>{paper.created}</span>
              </div>
            </button>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
