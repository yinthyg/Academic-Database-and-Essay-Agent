import { useEffect, useMemo, useState } from "react";
import { Trash2, RefreshCw, Search } from "lucide-react";
import { AppHeader } from "../components/app-header";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { useAuth } from "../lib/auth-context";
import * as api from "../lib/api";
import { useNavigate } from "react-router";

function formatBytes(bytes: number) {
  if (!Number.isFinite(bytes)) return "-";
  if (bytes < 1024) return `${bytes} B`;
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  const mb = kb / 1024;
  if (mb < 1024) return `${mb.toFixed(1)} MB`;
  const gb = mb / 1024;
  return `${gb.toFixed(1)} GB`;
}

export function Documents() {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const [docs, setDocs] = useState<api.Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");

  async function load() {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const list = await api.getDocuments(token);
      setDocs(list);
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return docs;
    return docs.filter((d) => `${d.id} ${d.original_name}`.toLowerCase().includes(q));
  }, [docs, query]);

  async function onDelete(docId: number) {
    if (!token) return;
    if (!confirm(`确认删除文献 ID=${docId} 吗？\n（会同时删除该文献的向量索引）`)) return;
    try {
      await api.deleteDocument(token, docId);
      setDocs((prev) => prev.filter((d) => d.id !== docId));
    } catch (e) {
      alert(e instanceof Error ? e.message : "删除失败");
    }
  }

  return (
    <div className="flex h-screen flex-col bg-white">
      <AppHeader />
      <div className="mx-auto w-full max-w-6xl flex-1 p-6">
        <div className="mb-6 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">文献管理</h1>
            <p className="mt-1 text-sm text-gray-600">
              {user?.is_admin ? "管理员可查看全部文献；普通用户仅能看到自己上传或共享的文献。" : "仅显示你可见的文献。"}
            </p>
          </div>
          <Button variant="outline" onClick={load} disabled={loading} className="gap-2">
            <RefreshCw className="size-4" />
            刷新
          </Button>
        </div>

        <Card className="p-4">
          <div className="mb-4 flex items-center gap-2">
            <div className="relative w-full max-w-md">
              <Search className="absolute left-2 top-2.5 size-4 text-gray-400" />
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="搜索：文献ID / 文件名"
                className="pl-8"
              />
            </div>
            <div className="text-sm text-gray-500">
              共 {filtered.length} / {docs.length} 条
            </div>
          </div>

          {error ? (
            <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
              {error}
            </div>
          ) : null}

          <div className="overflow-auto rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[80px]">ID</TableHead>
                  <TableHead>文件名</TableHead>
                  <TableHead className="w-[140px]">大小</TableHead>
                  <TableHead className="w-[120px]">权限</TableHead>
                  <TableHead className="w-[220px]">上传时间</TableHead>
                  <TableHead className="w-[120px] text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((d) => (
                  <TableRow
                    key={d.id}
                    className="cursor-pointer"
                    onClick={() => navigate(`/documents/${d.id}`)}
                  >
                    <TableCell className="font-medium">{d.id}</TableCell>
                    <TableCell className="max-w-[520px] truncate" title={d.original_name}>
                      <span className="text-blue-700 hover:underline">{d.original_name}</span>
                    </TableCell>
                    <TableCell>{formatBytes(d.size_bytes)}</TableCell>
                    <TableCell>{d.is_private ? "私有" : "共享"}</TableCell>
                    <TableCell>{new Date(d.created_at).toLocaleString()}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="destructive"
                        size="sm"
                        className="gap-2"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDelete(d.id);
                        }}
                      >
                        <Trash2 className="size-4" />
                        删除
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                {filtered.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="py-10 text-center text-sm text-gray-500">
                      {loading ? "加载中..." : "暂无文献"}
                    </TableCell>
                  </TableRow>
                ) : null}
              </TableBody>
            </Table>
          </div>
        </Card>
      </div>
    </div>
  );
}

