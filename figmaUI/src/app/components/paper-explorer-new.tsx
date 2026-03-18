import { useEffect, useState } from "react";
import { Search, FileText, ExternalLink, Loader2 } from "lucide-react";
import { Input } from "./ui/input";
import { ScrollArea } from "./ui/scroll-area";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { useAuth } from "../lib/auth-context";
import * as api from "../lib/api";

interface PaperExplorerNewProps {
  selectedPaperId: number | null;
  onPaperSelect: (id: number | null) => void;
}

export function PaperExplorerNew({ selectedPaperId, onPaperSelect }: PaperExplorerNewProps) {
  const { token } = useAuth();
  const [papers, setPapers] = useState<api.Paper[]>([]);
  const [paperProfile, setPaperProfile] = useState<api.PaperProfile | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);

  useEffect(() => {
    if (token) {
      loadPapers();
    }
  }, [token]);

  useEffect(() => {
    if (selectedPaperId && token) {
      loadPaperProfile();
    } else {
      setPaperProfile(null);
    }
  }, [selectedPaperId, token]);

  const loadPapers = async () => {
    if (!token) return;
    try {
      const data = await api.getPapers(token);
      setPapers(data);
    } catch (error) {
      console.error("Failed to load papers:", error);
    }
  };

  const loadPaperProfile = async () => {
    if (!token || !selectedPaperId) return;
    setIsLoadingProfile(true);
    try {
      const profile = await api.getPaperProfile(token, selectedPaperId);
      setPaperProfile(profile);
    } catch (error) {
      console.error("Failed to load paper profile:", error);
      setPaperProfile(null);
    } finally {
      setIsLoadingProfile(false);
    }
  };

  const filteredPapers = papers.filter((paper) => {
    const searchLower = searchQuery.toLowerCase();
    const title = paper.title || paper.file_path || "";
    return title.toLowerCase().includes(searchLower);
  });

  const selectedPaper = selectedPaperId
    ? papers.find((p) => p.id === selectedPaperId)
    : null;

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
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {!selectedPaperId ? (
        /* Paper List */
        <ScrollArea className="flex-1">
          <div className="p-4 space-y-3">
            {filteredPapers.map((paper) => (
              <button
                key={paper.id}
                onClick={() => onPaperSelect(paper.id)}
                className="w-full text-left p-3 bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-sm transition-all"
              >
                <div className="flex items-start gap-2 mb-2">
                  <FileText className="size-4 text-blue-600 mt-0.5 flex-shrink-0" />
                  <h3 className="text-sm font-medium text-gray-900 line-clamp-2">
                    {paper.title || paper.file_path || `Paper ${paper.id}`}
                  </h3>
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge variant="secondary" className="text-xs">
                    ID: {paper.id}
                  </Badge>
                  <span className="text-xs text-gray-500">
                    {new Date(paper.created_at).toLocaleDateString()}
                  </span>
                </div>
              </button>
            ))}

            {filteredPapers.length === 0 && (
              <div className="text-center py-8">
                <p className="text-sm text-gray-500">
                  {searchQuery ? "No matching papers" : "No papers available"}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  Upload documents to see them here
                </p>
              </div>
            )}
          </div>
        </ScrollArea>
      ) : (
        /* Paper Detail View */
        <div className="flex-1 flex flex-col">
          <div className="p-4 border-b border-gray-200 bg-white">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onPaperSelect(null)}
              className="mb-3"
            >
              ← Back to list
            </Button>
            <div className="flex items-start gap-2">
              <FileText className="size-5 text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-gray-900 mb-2">
                  {selectedPaper?.title || selectedPaper?.file_path || `Paper ${selectedPaperId}`}
                </h3>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary" className="text-xs">
                    ID: {selectedPaperId}
                  </Badge>
                </div>
              </div>
            </div>
          </div>

          {isLoadingProfile ? (
            <div className="flex-1 flex items-center justify-center">
              <Loader2 className="size-6 animate-spin text-gray-400" />
            </div>
          ) : (
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
                    {paperProfile ? (
                      <>
                        {paperProfile.title && (
                          <Section title="Title" content={paperProfile.title} />
                        )}
                        {paperProfile.authors && paperProfile.authors.length > 0 && (
                          <Section
                            title="Authors"
                            content={paperProfile.authors.join(", ")}
                          />
                        )}
                        {paperProfile.abstract && (
                          <Section title="Abstract" content={paperProfile.abstract} />
                        )}
                        {paperProfile.method && (
                          <Section title="Method" content={paperProfile.method} />
                        )}
                        {paperProfile.experiment && (
                          <Section title="Experiment" content={paperProfile.experiment} />
                        )}
                        {paperProfile.conclusion && (
                          <Section title="Conclusion" content={paperProfile.conclusion} />
                        )}
                        {paperProfile.venue && (
                          <Section title="Venue" content={paperProfile.venue} />
                        )}
                        {paperProfile.year && (
                          <Section title="Year" content={String(paperProfile.year)} />
                        )}
                      </>
                    ) : (
                      <div className="text-center py-8 text-sm text-gray-500">
                        No structured information available
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </TabsContent>

              <TabsContent value="json" className="flex-1 mt-0">
                <ScrollArea className="h-full">
                  <div className="p-4">
                    <pre className="text-xs bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto font-mono">
                      {JSON.stringify(paperProfile, null, 2)}
                    </pre>
                  </div>
                </ScrollArea>
              </TabsContent>
            </Tabs>
          )}
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
