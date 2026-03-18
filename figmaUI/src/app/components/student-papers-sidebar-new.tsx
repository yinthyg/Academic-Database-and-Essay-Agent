import { useEffect, useState } from "react";
import { Plus, FileEdit, ArrowLeft, User, LogOut, Upload, Library, Shield } from "lucide-react";
import { Button } from "./ui/button";
import { ScrollArea } from "./ui/scroll-area";
import { Link } from "react-router";
import { useAuth } from "../lib/auth-context";
import * as api from "../lib/api";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "./ui/dialog";
import { Input } from "./ui/input";
import { Label } from "./ui/label";

interface StudentPapersSidebarNewProps {
  activePaperId: number | null;
  onPaperSelect: (id: number) => void;
  onPapersChange: () => void;
}

export function StudentPapersSidebarNew({
  activePaperId,
  onPaperSelect,
  onPapersChange,
}: StudentPapersSidebarNewProps) {
  const { token, user, logout } = useAuth();
  const [papers, setPapers] = useState<api.StudentPaper[]>([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    loadPapers();
  }, [token]);

  const loadPapers = async () => {
    if (!token) return;
    try {
      const data = await api.getStudentPapers(token);
      setPapers(data);
      
      // Auto-select first paper if none selected
      if (!activePaperId && data.length > 0) {
        onPaperSelect(data[0].id);
      }
    } catch (error) {
      console.error("Failed to load student papers:", error);
    }
  };

  const handleCreatePaper = async () => {
    if (!token || !newTitle.trim()) return;
    setIsCreating(true);

    try {
      const newPaper = await api.createStudentPaper(token, newTitle);
      await loadPapers();
      onPaperSelect(newPaper.id);
      onPapersChange();
      setNewTitle("");
      setIsDialogOpen(false);
    } catch (error) {
      console.error("Failed to create paper:", error);
    } finally {
      setIsCreating(false);
    }
  };

  const countWords = (content?: string) => {
    if (!content) return 0;
    return content.trim().split(/\s+/).filter(Boolean).length;
  };

  return (
    <div className="w-64 border-r border-gray-200 flex flex-col bg-gray-50">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <h1 className="text-lg font-semibold text-gray-900 mb-1">My Papers</h1>
        <p className="text-xs text-gray-500">Student Writing Workspace</p>
      </div>

      {/* User Info */}
      <div className="p-3 border-b border-gray-200 bg-white">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center">
            <User className="size-4 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">{user?.username}</p>
            <p className="text-xs text-gray-500">
              {user?.is_admin ? "Admin" : "User"}
            </p>
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="w-full justify-start gap-2"
          onClick={logout}
        >
          <LogOut className="size-4" />
          Logout
        </Button>
      </div>

      {/* Navigation */}
      <div className="p-3 border-b border-gray-200 bg-white">
        <div className="space-y-2">
          <Link to="/">
            <Button variant="outline" size="sm" className="w-full justify-start gap-2">
              <ArrowLeft className="size-4" />
              文献问答
            </Button>
          </Link>
          <Link to="/documents/upload">
            <Button variant="outline" size="sm" className="w-full justify-start gap-2">
              <Upload className="size-4" />
              文献上传
            </Button>
          </Link>
          <Link to="/documents">
            <Button variant="outline" size="sm" className="w-full justify-start gap-2">
              <Library className="size-4" />
              文献管理
            </Button>
          </Link>
          {user?.is_admin ? (
            <Link to="/admin">
              <Button variant="outline" size="sm" className="w-full justify-start gap-2">
                <Shield className="size-4" />
                管理员后台
              </Button>
            </Link>
          ) : null}
        </div>
      </div>

      {/* New Paper Button */}
      <div className="p-3">
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="w-full justify-start gap-2" variant="default">
              <Plus className="size-4" />
              New Paper
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Paper</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 pt-4">
              <div className="space-y-2">
                <Label htmlFor="title">Paper Title</Label>
                <Input
                  id="title"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g., A Survey on Transformer Architectures"
                  required
                />
              </div>
              <Button
                onClick={handleCreatePaper}
                disabled={isCreating || !newTitle.trim()}
                className="w-full"
              >
                {isCreating ? "Creating..." : "Create"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Papers List */}
      <ScrollArea className="flex-1">
        <div className="p-3 space-y-2">
          {papers.map((paper) => (
            <button
              key={paper.id}
              onClick={() => onPaperSelect(paper.id)}
              className={`w-full text-left p-3 rounded-lg border transition-all ${
                activePaperId === paper.id
                  ? "bg-white border-purple-200 shadow-sm"
                  : "bg-white border-gray-200 hover:border-gray-300 hover:shadow-sm"
              }`}
            >
              <div className="flex items-start gap-2 mb-2">
                <FileEdit className="size-4 text-purple-600 mt-0.5 flex-shrink-0" />
                <h3 className="text-sm font-medium text-gray-900 line-clamp-2">
                  {paper.title}
                </h3>
              </div>
              <div className="flex items-center justify-between text-xs text-gray-500 mt-2">
                <span>{countWords(paper.content)} words</span>
                <span>{new Date(paper.created_at).toLocaleDateString()}</span>
              </div>
            </button>
          ))}

          {papers.length === 0 && (
            <div className="text-center py-8">
              <p className="text-sm text-gray-500">No papers yet</p>
              <p className="text-xs text-gray-400 mt-1">Create one to get started</p>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
