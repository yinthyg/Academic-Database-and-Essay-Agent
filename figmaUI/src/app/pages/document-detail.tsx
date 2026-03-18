import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router";
import { FileText, Loader2, Search } from "lucide-react";
import { AppHeader } from "../components/app-header";
import { Card } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { ScrollArea } from "../components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { useAuth } from "../lib/auth-context";
import * as api from "../lib/api";

function Field({ label, value }: { label: string; value?: string }) {
  return (
    <div className="rounded-lg border bg-white p-3">
      <div className="text-xs font-medium text-gray-500">{label}</div>
      <div className="mt-1 whitespace-pre-wrap text-sm text-gray-900">{value?.trim() ? value : "-"}</div>
    </div>
  );
}

export function DocumentDetail() {
  const { token } = useAuth();
  const params = useParams();
  const documentId = Number(params.documentId);

  const [doc, setDoc] = useState<api.Document | null>(null);
  const [docError, setDocError] = useState("");
  const [loadingDoc, setLoadingDoc] = useState(false);

  const [text, setText] = useState<string>("");
  const [textLoading, setTextLoading] = useState(false);

  const [chunkQuery, setChunkQuery] = useState("");
  const [chunks, setChunks] = useState<{ chunk_index: number; text: string }[]>([]);
  const [chunksTotal, setChunksTotal] = useState(0);
  const [chunksLoading, setChunksLoading] = useState(false);

  const [analysis, setAnalysis] = useState<api.DocumentAnalysisResponse | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);

  const fileUrl = useMemo(() => {
    if (!token || !Number.isFinite(documentId)) return "";
    return api.documentFileUrl(documentId, token);
  }, [documentId, token]);

  useEffect(() => {
    async function load() {
      if (!token || !Number.isFinite(documentId)) return;
      setLoadingDoc(true);
      setDocError("");
      try {
        const d = await api.getDocument(token, documentId);
        setDoc(d);
      } catch (e) {
        setDocError(e instanceof Error ? e.message : "加载失败");
      } finally {
        setLoadingDoc(false);
      }
    }
    load();
  }, [token, documentId]);

  useEffect(() => {
    async function loadText() {
      if (!token || !Number.isFinite(documentId)) return;
      setTextLoading(true);
      try {
        const res = await api.getDocumentText(token, documentId, { limitChars: 200000 });
        setText(res.text || "");
      } catch {
        setText("");
      } finally {
        setTextLoading(false);
      }
    }
    loadText();
  }, [token, documentId]);

  useEffect(() => {
    async function loadChunks() {
      if (!token || !Number.isFinite(documentId)) return;
      setChunksLoading(true);
      try {
        const res = await api.getDocumentChunks(token, documentId, { q: chunkQuery.trim() || undefined, limit: 500 });
        setChunks(res.chunks || []);
        setChunksTotal(res.total || 0);
      } catch {
        setChunks([]);
        setChunksTotal(0);
      } finally {
        setChunksLoading(false);
      }
    }
    loadChunks();
  }, [token, documentId, chunkQuery]);

  useEffect(() => {
    async function loadAnalysis() {
      if (!token || !Number.isFinite(documentId)) return;
      setAnalysisLoading(true);
      try {
        const res = await api.getDocumentAnalysis(token, documentId);
        setAnalysis(res);
      } catch (e) {
        setAnalysis({
          document_id: documentId,
          status: "error",
          detail: e instanceof Error ? e.message : "加载失败",
        });
      } finally {
        setAnalysisLoading(false);
      }
    }
    loadAnalysis();
  }, [token, documentId]);

  return (
    <div className="flex h-screen flex-col bg-white">
      <AppHeader />
      <div className="mx-auto flex w-full max-w-[1400px] min-h-0 flex-1 flex-col p-4">
        <div className="mb-4 flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="text-xs text-gray-500">文献详情</div>
            <h1 className="mt-1 truncate text-2xl font-semibold text-gray-900">
              {loadingDoc ? "加载中..." : doc?.original_name || `文献 #${documentId}`}
            </h1>
            {docError ? <div className="mt-2 text-sm text-red-700">{docError}</div> : null}
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => window.open(fileUrl || "#", "_blank")} disabled={!fileUrl}>
              打开原文件
            </Button>
          </div>
        </div>

        <div className="flex min-h-0 flex-1 gap-4">
          {/* Left: full content */}
          <Card className="flex min-h-0 flex-1 flex-col p-3">
            <div className="mb-2 flex items-center gap-2">
              <FileText className="size-4 text-gray-500" />
              <div className="text-sm font-semibold text-gray-900">文献全文</div>
            </div>

            <Tabs defaultValue="preview" className="min-h-0 flex-1">
              <TabsList>
                <TabsTrigger value="preview">预览</TabsTrigger>
                <TabsTrigger value="text">提取文本</TabsTrigger>
              </TabsList>

              <TabsContent value="preview" className="min-h-0 flex-1">
                <div className="h-full overflow-hidden rounded-lg border bg-gray-50">
                  {fileUrl ? (
                    <object data={fileUrl} type={doc?.mime_type || undefined} className="h-full w-full">
                      <div className="p-4 text-sm text-gray-600">无法直接预览该格式，请点击右上角“打开原文件”。</div>
                    </object>
                  ) : (
                    <div className="p-4 text-sm text-gray-600">暂无可预览内容</div>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="text" className="min-h-0 flex-1">
                <div className="h-full overflow-hidden rounded-lg border bg-white">
                  {textLoading ? (
                    <div className="flex items-center gap-2 p-4 text-sm text-gray-600">
                      <Loader2 className="size-4 animate-spin" />
                      提取中...
                    </div>
                  ) : (
                    <ScrollArea className="h-full">
                      <pre className="whitespace-pre-wrap break-words p-4 text-sm text-gray-900">
                        {text?.trim() ? text : "（未提取到文本，建议打开原文件查看）"}
                      </pre>
                    </ScrollArea>
                  )}
                </div>
              </TabsContent>
            </Tabs>
          </Card>

          {/* Right: two panels */}
          <div className="flex min-h-0 w-[520px] flex-col gap-4">
            {/* Top-right: chunks */}
            <Card className="flex min-h-0 flex-1 flex-col p-3">
              <div className="mb-2 flex items-center justify-between gap-2">
                <div className="text-sm font-semibold text-gray-900">RAG 切片预览</div>
                <div className="text-xs text-gray-500">
                  {chunksLoading ? "加载中..." : `${chunks.length} / ${chunksTotal}`}
                </div>
              </div>
              <div className="mb-3 flex items-center gap-2">
                <div className="relative w-full">
                  <Search className="absolute left-2 top-2.5 size-4 text-gray-400" />
                  <Input
                    value={chunkQuery}
                    onChange={(e) => setChunkQuery(e.target.value)}
                    placeholder="搜索切片内容"
                    className="pl-8"
                  />
                </div>
              </div>

              <div className="min-h-0 flex-1 overflow-hidden rounded-lg border">
                <ScrollArea className="h-full">
                  <div className="divide-y">
                    {chunks.map((c) => (
                      <div key={c.chunk_index} className="p-3 hover:bg-gray-50">
                        <div className="text-xs font-medium text-gray-500">块 #{c.chunk_index}</div>
                        <div className="mt-1 line-clamp-4 whitespace-pre-wrap text-sm text-gray-900">{c.text}</div>
                      </div>
                    ))}
                    {!chunksLoading && chunks.length === 0 ? (
                      <div className="p-4 text-sm text-gray-600">暂无切片（可能仍在索引/解析中）</div>
                    ) : null}
                  </div>
                </ScrollArea>
              </div>
            </Card>

            {/* Bottom-right: structured analysis */}
            <Card className="flex min-h-0 flex-1 flex-col p-3">
              <div className="mb-2 flex items-center justify-between gap-2">
                <div className="text-sm font-semibold text-gray-900">结构化解析（20条）</div>
                {analysisLoading ? (
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <Loader2 className="size-3 animate-spin" />
                    加载中
                  </div>
                ) : null}
              </div>

              {analysis?.status === "pending" ? (
                <div className="rounded-lg border bg-gray-50 p-4 text-sm text-gray-700">正在解析中...</div>
              ) : analysis?.status === "error" ? (
                <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
                  加载失败：{analysis.detail || "unknown error"}
                </div>
              ) : null}

              {analysis?.status === "ready" && analysis.analysis ? (
                <ScrollArea className="min-h-0 flex-1">
                  <div className="grid gap-3">
                    <Card className="p-3">
                      <div className="text-sm font-semibold text-gray-900">元数据</div>
                      <div className="mt-3 grid gap-3 md:grid-cols-2">
                        <Field label="作者" value={analysis.analysis.metadata.authors} />
                        <Field label="发表年份" value={analysis.analysis.metadata.year} />
                        <Field label="论文标题" value={analysis.analysis.metadata.title} />
                        <Field label="期刊/会议名称" value={analysis.analysis.metadata.venue} />
                        <Field label="卷号" value={analysis.analysis.metadata.volume} />
                        <Field label="期号" value={analysis.analysis.metadata.issue} />
                        <Field label="起止页码" value={analysis.analysis.metadata.pages} />
                        <Field label="DOI号" value={analysis.analysis.metadata.doi} />
                      </div>
                    </Card>

                    <Field label="核心问题" value={analysis.analysis.core_problem} />
                    <Field label="核心假设" value={analysis.analysis.core_hypothesis} />
                    <Field label="研究设计" value={analysis.analysis.research_design} />
                    <Field label="数据来源" value={analysis.analysis.data_source} />
                    <Field label="方法与技术" value={analysis.analysis.methods_and_tech} />
                    <Field label="分析流程" value={analysis.analysis.analysis_workflow} />
                    <Field label="数据分析" value={analysis.analysis.data_analysis} />
                    <Field label="核心发现" value={analysis.analysis.core_findings} />
                    <Field label="实验结果" value={analysis.analysis.experimental_results} />
                    <Field label="辅助结果" value={analysis.analysis.supporting_results} />
                    <Field label="最终结论" value={analysis.analysis.final_conclusion} />
                    <Field label="领域贡献" value={analysis.analysis.field_contribution} />
                    <Field label="与我研究的相关性" value={analysis.analysis.relevance_to_my_research} />
                    <Field label="亮点分析" value={analysis.analysis.highlights_analysis} />

                    <div className="rounded-lg border bg-white p-3">
                      <div className="text-xs font-medium text-gray-500">图表索引</div>
                      <pre className="mt-2 whitespace-pre-wrap break-words text-sm text-gray-900">
                        {JSON.stringify(analysis.analysis.figures_tables_index || [], null, 2)}
                      </pre>
                    </div>

                    <Field label="个人评价" value={analysis.analysis.personal_evaluation} />
                    <Field label="疑问记录" value={analysis.analysis.questions_log} />
                    <Field label="启发思考" value={analysis.analysis.inspiration_thoughts} />

                    <div className="rounded-lg border bg-white p-3">
                      <div className="text-xs font-medium text-gray-500">参考文献（代表性1-2条）</div>
                      <pre className="mt-2 whitespace-pre-wrap break-words text-sm text-gray-900">
                        {JSON.stringify(analysis.analysis.representative_references || [], null, 2)}
                      </pre>
                    </div>
                  </div>
                </ScrollArea>
              ) : null}
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

