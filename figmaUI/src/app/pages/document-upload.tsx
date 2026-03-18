import { useMemo, useState } from "react";
import { UploadCloud } from "lucide-react";
import { AppHeader } from "../components/app-header";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Switch } from "../components/ui/switch";
import { useAuth } from "../lib/auth-context";
import * as api from "../lib/api";

export function DocumentUpload() {
  const { token } = useAuth();
  const [files, setFiles] = useState<File[]>([]);
  const [isPrivate, setIsPrivate] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string>("");
  const [result, setResult] = useState<api.BatchUploadResponse | null>(null);

  const accept = useMemo(() => ".pdf,.txt,.docx,.xlsx", []);

  async function onUpload() {
    if (!token) return;
    if (!files.length) {
      setError("请选择要上传的文件（PDF/TXT/DOCX/XLSX），支持 Shift 多选批量上传");
      return;
    }
    setError("");
    setResult(null);
    setIsUploading(true);
    try {
      const res =
        files.length === 1
          ? {
              total: 1,
              success: 1,
              failed: 0,
              items: [
                {
                  filename: files[0].name,
                  ok: true,
                  document: await api.uploadDocument(token, files[0], isPrivate),
                },
              ],
            }
          : await api.uploadDocumentsBatch(token, files, isPrivate, { rollbackOnError: false });

      setResult(res);
      setFiles([]);
      const el = document.getElementById("file-input") as HTMLInputElement | null;
      if (el) el.value = "";
    } catch (e) {
      setError(e instanceof Error ? e.message : "上传失败");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className="flex h-screen flex-col bg-white">
      <AppHeader />
      <div className="mx-auto w-full max-w-5xl flex-1 p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-gray-900">文献上传（入库 RAG）</h1>
          <p className="mt-1 text-sm text-gray-600">
            上传后会自动解析并写入向量索引，用于后续文献问答与对比。
          </p>
        </div>

        <Card className="p-6">
          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="file-input">文件</Label>
              <Input
                id="file-input"
                type="file"
                accept={accept}
                multiple
                onChange={(e) => setFiles(Array.from(e.target.files || []))}
                disabled={isUploading}
              />
              <div className="text-xs text-gray-500">支持：PDF / TXT / DOCX / XLSX（可 Shift 多选批量上传）</div>
            </div>

            <div className="space-y-2">
              <Label>权限</Label>
              <div className="flex items-center justify-between rounded-lg border p-3">
                <div>
                  <div className="text-sm font-medium text-gray-900">
                    {isPrivate ? "私有（仅自己可见）" : "共享（所有人可见）"}
                  </div>
                  <div className="text-xs text-gray-500">可在“文献管理”中查看与删除</div>
                </div>
                <Switch checked={!isPrivate} onCheckedChange={(v) => setIsPrivate(!v)} disabled={isUploading} />
              </div>
            </div>
          </div>

          {error ? (
            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
              {error}
            </div>
          ) : null}

          {result ? (
            <div className="mt-4 rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-800">
              上传完成：成功 {result.success} / {result.total}，失败 {result.failed}。
            </div>
          ) : null}

          {result?.items?.length ? (
            <div className="mt-3 rounded-lg border bg-white p-3">
              <div className="text-sm font-medium text-gray-900">结果明细</div>
              <div className="mt-2 space-y-2">
                {result.items.map((it, idx) => (
                  <div key={`${it.filename}-${idx}`} className="flex items-start justify-between gap-3 rounded border p-2">
                    <div className="min-w-0">
                      <div className="truncate text-sm text-gray-900">{it.filename}</div>
                      {it.ok && it.document ? (
                        <div className="text-xs text-gray-500">ID: {it.document.id} · {it.document.original_name}</div>
                      ) : (
                        <div className="text-xs text-red-700">{it.error || "上传失败"}</div>
                      )}
                    </div>
                    <div className={`text-xs font-medium ${it.ok ? "text-green-700" : "text-red-700"}`}>
                      {it.ok ? "成功" : "失败"}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          <div className="mt-6 flex items-center gap-3">
            <Button onClick={onUpload} disabled={isUploading || files.length === 0}>
              <UploadCloud className="mr-2 size-4" />
              {isUploading ? "上传中..." : "上传并入库"}
            </Button>
            <div className="text-xs text-gray-500">
              若同名文件重复上传，会覆盖并重建该文献的向量索引。
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

