import { useState, useEffect, useCallback } from "react";
import { Save, Check, Loader2 } from "lucide-react";
import { Textarea } from "./ui/textarea";
import { Badge } from "./ui/badge";
import { useAuth } from "../lib/auth-context";
import * as api from "../lib/api";

interface PaperEditorNewProps {
  paperId: number | null;
}

export function PaperEditorNew({ paperId }: PaperEditorNewProps) {
  const { token } = useAuth();
  const [paper, setPaper] = useState<api.StudentPaper | null>(null);
  const [content, setContent] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    if (paperId && token) {
      loadPaper();
    } else {
      setPaper(null);
      setContent("");
    }
  }, [paperId, token]);

  // Auto-save functionality
  useEffect(() => {
    if (!paperId || !token || !paper) return;

    const timer = setTimeout(() => {
      savePaper();
    }, 2000); // Auto-save after 2 seconds of no typing

    return () => clearTimeout(timer);
  }, [content, paperId, token, paper]);

  const loadPaper = async () => {
    if (!token || !paperId) return;
    try {
      const data = await api.getStudentPaper(token, paperId);
      setPaper(data);
      setContent(data.content || "");
    } catch (error) {
      console.error("Failed to load paper:", error);
    }
  };

  const savePaper = async () => {
    if (!token || !paperId || !paper) return;
    
    // Only save if content has changed
    if (content === paper.content) return;

    setIsSaving(true);
    setSaveError(null);

    try {
      await api.saveStudentPaper(token, paperId, content);
      setLastSaved(new Date());
      // Update local paper state
      setPaper((prev) => (prev ? { ...prev, content } : null));
    } catch (error) {
      console.error("Failed to save paper:", error);
      setSaveError(error instanceof Error ? error.message : "Save failed");
    } finally {
      setIsSaving(false);
    }
  };

  const countWords = (text: string) => {
    return text.trim().split(/\s+/).filter(Boolean).length;
  };

  if (!paperId) {
    return (
      <div className="flex-1 flex items-center justify-center bg-white">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Welcome to Paper Workspace
          </h2>
          <p className="text-gray-500">Select a paper or create a new one to start writing</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold text-gray-900">
            {paper?.title || "Loading..."}
          </h2>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="text-xs">
              {countWords(content)} words
            </Badge>
            <div className="flex items-center gap-2 text-xs">
              {isSaving ? (
                <span className="text-gray-500 flex items-center gap-1">
                  <Save className="size-3 animate-pulse" />
                  Saving...
                </span>
              ) : saveError ? (
                <span className="text-red-600 flex items-center gap-1">
                  Error: {saveError}
                </span>
              ) : lastSaved ? (
                <span className="text-green-600 flex items-center gap-1">
                  <Check className="size-3" />
                  Saved {lastSaved.toLocaleTimeString()}
                </span>
              ) : (
                <span className="text-gray-500">Ready</span>
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
            className="min-h-[calc(100vh-250px)] font-mono text-sm border-none focus-visible:ring-0 focus-visible:ring-offset-0 resize-none"
            placeholder="Start writing your paper here...

# Your Paper Title

## Abstract

Write your abstract here...

## 1. Introduction

Start your introduction..."
          />
        </div>
      </div>

      {/* Section Navigation */}
      <div className="border-t border-gray-200 px-4 py-2 bg-gray-50">
        <div className="max-w-4xl mx-auto flex gap-2 overflow-x-auto">
          {["Abstract", "Introduction", "Method", "Experiments", "Conclusion", "References"].map(
            (section) => (
              <button
                key={section}
                className="px-3 py-1 text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded whitespace-nowrap"
                onClick={() => {
                  // Scroll to section in content (simplified)
                  const textarea = document.querySelector("textarea");
                  if (textarea) {
                    const sectionText = `## ${section}`;
                    const index = content.indexOf(sectionText);
                    if (index !== -1) {
                      textarea.focus();
                      textarea.setSelectionRange(index, index);
                    }
                  }
                }}
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
