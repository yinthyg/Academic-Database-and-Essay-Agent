import { useEffect, useMemo, useState } from "react";
import { Plus, RefreshCw, Search, Trash2, KeyRound } from "lucide-react";
import { AppHeader } from "../components/app-header";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Switch } from "../components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "../components/ui/dialog";
import { useAuth } from "../lib/auth-context";
import * as api from "../lib/api";

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

export function Admin() {
  const { token } = useAuth();
  const [dashboard, setDashboard] = useState<api.DashboardData | null>(null);
  const [users, setUsers] = useState<api.AdminUser[]>([]);
  const [history, setHistory] = useState<api.HistoryItem[]>([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [historyQuery, setHistoryQuery] = useState("");
  const [historyLoading, setHistoryLoading] = useState(false);

  // Create user dialog state
  const [newUsername, setNewUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newIsAdmin, setNewIsAdmin] = useState(false);
  const [creating, setCreating] = useState(false);

  // Reset password dialog state
  const [resetUserId, setResetUserId] = useState<number | null>(null);
  const [resetPassword, setResetPassword] = useState("");
  const [resetting, setResetting] = useState(false);

  async function loadAll() {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const [d, u] = await Promise.all([api.getDashboard(token), api.adminListUsers(token)]);
      setDashboard(d);
      setUsers(u);
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }

  async function loadHistory(q?: string) {
    if (!token) return;
    setHistoryLoading(true);
    try {
      const list = await api.getHistory(token, q?.trim() ? q.trim() : undefined);
      setHistory(list);
    } catch (e) {
      alert(e instanceof Error ? e.message : "加载历史失败");
    } finally {
      setHistoryLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
    loadHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const userCountText = useMemo(() => `${users.length} 个账号`, [users.length]);

  async function onCreateUser() {
    if (!token) return;
    if (!newUsername.trim() || !newPassword) {
      alert("请填写用户名和密码");
      return;
    }
    setCreating(true);
    try {
      await api.adminCreateUser(token, {
        username: newUsername.trim(),
        password: newPassword,
        is_admin: newIsAdmin,
      });
      setNewUsername("");
      setNewPassword("");
      setNewIsAdmin(false);
      await loadAll();
    } catch (e) {
      alert(e instanceof Error ? e.message : "创建失败");
    } finally {
      setCreating(false);
    }
  }

  async function onResetPassword() {
    if (!token || resetUserId == null) return;
    if (!resetPassword) {
      alert("请输入新密码");
      return;
    }
    setResetting(true);
    try {
      await api.adminResetUserPassword(token, resetUserId, resetPassword);
      setResetPassword("");
      setResetUserId(null);
      await loadAll();
    } catch (e) {
      alert(e instanceof Error ? e.message : "重置失败");
    } finally {
      setResetting(false);
    }
  }

  async function onCleanupHistory() {
    if (!token) return;
    if (!confirm("确认清理历史记录吗？（会按后端保留策略删除过期数据）")) return;
    try {
      const res = await api.adminCleanupHistory(token);
      alert(`已清理 ${res.deleted} 条`);
      await loadHistory(historyQuery);
    } catch (e) {
      alert(e instanceof Error ? e.message : "清理失败");
    }
  }

  return (
    <div className="flex h-screen flex-col bg-white">
      <AppHeader />
      <div className="mx-auto w-full max-w-7xl flex-1 p-6">
        <div className="mb-6 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">管理员后台</h1>
            <p className="mt-1 text-sm text-gray-600">账号管理、系统概览、历史记录审计</p>
          </div>
          <Button variant="outline" onClick={loadAll} disabled={loading} className="gap-2">
            <RefreshCw className="size-4" />
            刷新
          </Button>
        </div>

        {error ? (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
            {error}
          </div>
        ) : null}

        {/* Dashboard */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="p-4">
            <div className="text-sm text-gray-500">文献总数</div>
            <div className="mt-1 text-2xl font-semibold text-gray-900">{dashboard?.total_documents ?? "-"}</div>
            <div className="mt-2 text-xs text-gray-500">存储：{dashboard ? formatBytes(dashboard.total_storage_bytes) : "-"}</div>
          </Card>
          <Card className="p-4">
            <div className="text-sm text-gray-500">账号 / 群组</div>
            <div className="mt-1 text-2xl font-semibold text-gray-900">
              {dashboard?.total_users ?? "-"} / {dashboard?.total_groups ?? "-"}
            </div>
            <div className="mt-2 text-xs text-gray-500">{userCountText}</div>
          </Card>
          <Card className="p-4">
            <div className="text-sm text-gray-500">近 {""}N 天提问数</div>
            <div className="mt-1 text-2xl font-semibold text-gray-900">{dashboard?.recent_questions ?? "-"}</div>
            <div className="mt-2 text-xs text-gray-500">用于观察活跃度</div>
          </Card>
        </div>

        {/* Users */}
        <div className="mt-8">
          <div className="mb-3 flex items-center justify-between">
            <div className="text-lg font-semibold text-gray-900">账号管理</div>
            <Dialog>
              <DialogTrigger asChild>
                <Button className="gap-2">
                  <Plus className="size-4" />
                  创建账号
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[520px]">
                <DialogHeader>
                  <DialogTitle>创建账号</DialogTitle>
                </DialogHeader>
                <div className="grid gap-4">
                  <div className="grid gap-2">
                    <Label>用户名</Label>
                    <Input value={newUsername} onChange={(e) => setNewUsername(e.target.value)} />
                  </div>
                  <div className="grid gap-2">
                    <Label>初始密码</Label>
                    <Input value={newPassword} onChange={(e) => setNewPassword(e.target.value)} type="password" />
                  </div>
                  <div className="flex items-center justify-between rounded-lg border p-3">
                    <div>
                      <div className="text-sm font-medium text-gray-900">设为管理员</div>
                      <div className="text-xs text-gray-500">管理员可访问后台与所有文献</div>
                    </div>
                    <Switch checked={newIsAdmin} onCheckedChange={setNewIsAdmin} />
                  </div>
                </div>
                <DialogFooter>
                  <Button onClick={onCreateUser} disabled={creating}>
                    {creating ? "创建中..." : "创建"}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          <Card className="p-4">
            <div className="overflow-auto rounded-lg border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[80px]">ID</TableHead>
                    <TableHead>用户名</TableHead>
                    <TableHead className="w-[120px]">角色</TableHead>
                    <TableHead className="w-[220px]">创建时间</TableHead>
                    <TableHead className="w-[180px] text-right">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((u) => (
                    <TableRow key={u.id}>
                      <TableCell className="font-medium">{u.id}</TableCell>
                      <TableCell>{u.username}</TableCell>
                      <TableCell>{u.is_admin ? "admin" : "user"}</TableCell>
                      <TableCell>{new Date(u.created_at).toLocaleString()}</TableCell>
                      <TableCell className="text-right">
                        <Dialog open={resetUserId === u.id} onOpenChange={(open) => setResetUserId(open ? u.id : null)}>
                          <DialogTrigger asChild>
                            <Button variant="outline" size="sm" className="gap-2">
                              <KeyRound className="size-4" />
                              重置密码
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="sm:max-w-[520px]">
                            <DialogHeader>
                              <DialogTitle>重置密码：{u.username}</DialogTitle>
                            </DialogHeader>
                            <div className="grid gap-2">
                              <Label>新密码</Label>
                              <Input
                                value={resetPassword}
                                onChange={(e) => setResetPassword(e.target.value)}
                                type="password"
                              />
                            </div>
                            <DialogFooter>
                              <Button onClick={onResetPassword} disabled={resetting}>
                                {resetting ? "提交中..." : "确认重置"}
                              </Button>
                            </DialogFooter>
                          </DialogContent>
                        </Dialog>
                      </TableCell>
                    </TableRow>
                  ))}
                  {users.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="py-10 text-center text-sm text-gray-500">
                        {loading ? "加载中..." : "暂无账号"}
                      </TableCell>
                    </TableRow>
                  ) : null}
                </TableBody>
              </Table>
            </div>
          </Card>
        </div>

        {/* History */}
        <div className="mt-8">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div className="text-lg font-semibold text-gray-900">历史记录（当前登录用户）</div>
            <div className="flex items-center gap-2">
              <Button variant="outline" onClick={onCleanupHistory} className="gap-2">
                <Trash2 className="size-4" />
                清理过期
              </Button>
            </div>
          </div>

          <Card className="p-4">
            <div className="mb-4 flex items-center gap-2">
              <div className="relative w-full max-w-md">
                <Search className="absolute left-2 top-2.5 size-4 text-gray-400" />
                <Input
                  value={historyQuery}
                  onChange={(e) => setHistoryQuery(e.target.value)}
                  placeholder="搜索问题/回答关键字"
                  className="pl-8"
                />
              </div>
              <Button
                variant="outline"
                onClick={() => loadHistory(historyQuery)}
                disabled={historyLoading}
              >
                {historyLoading ? "搜索中..." : "搜索"}
              </Button>
              <Button variant="ghost" onClick={() => { setHistoryQuery(""); loadHistory(); }} disabled={historyLoading}>
                清空
              </Button>
              <div className="text-sm text-gray-500">共 {history.length} 条</div>
            </div>

            <div className="overflow-auto rounded-lg border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[80px]">ID</TableHead>
                    <TableHead>问题</TableHead>
                    <TableHead className="w-[220px]">时间</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {history.map((h) => (
                    <TableRow key={h.id}>
                      <TableCell className="font-medium">{h.id}</TableCell>
                      <TableCell className="max-w-[860px]">
                        <div className="font-medium text-gray-900">{h.question}</div>
                        {h.answer ? <div className="mt-1 line-clamp-2 text-sm text-gray-600">{h.answer}</div> : null}
                      </TableCell>
                      <TableCell>{new Date(h.created_at).toLocaleString()}</TableCell>
                    </TableRow>
                  ))}
                  {history.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={3} className="py-10 text-center text-sm text-gray-500">
                        {historyLoading ? "加载中..." : "暂无历史记录"}
                      </TableCell>
                    </TableRow>
                  ) : null}
                </TableBody>
              </Table>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

