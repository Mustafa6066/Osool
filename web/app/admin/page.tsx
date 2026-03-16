'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Activity,
  ArrowLeft,
  Bot,
  Building2,
  ChevronRight,
  Clock3,
  Database,
  Loader2,
  MessageSquare,
  RefreshCw,
  Search,
  Send,
  Shield,
  Ticket as TicketIcon,
  TrendingUp,
  User as UserIcon,
  Users,
  Zap,
  FileText,
} from 'lucide-react';
import AdminShell from '@/components/AdminShell';
import { useAuth } from '@/contexts/AuthContext';
import {
  addAdminTicketReply,
  blockUser,
  getAdminConversation,
  getAdminConversations,
  getAdminDashboard,
  getAdminMarketIndicators,
  getAdminTicketDetail,
  getAdminTickets,
  getAdminUsers,
  getTicketStats,
  triggerEconomicScraper,
  triggerPropertyScraper,
  updateAdminMarketIndicator,
  updateTicketStatus,
  updateUserRole,
  getMarketingMaterials,
  generateMarketingMaterials,
  type MarketingMaterial,
  type AdminConversation,
  type AdminDashboardData,
  type AdminMessage,
  type AdminTicket,
  type AdminTicketDetail,
  type AdminUser,
  type TicketStats,
} from '@/lib/api';

type Tab = 'overview' | 'conversations' | 'users' | 'tickets' | 'scrapers' | 'marketing';

type ConversationDetail = {
  session_id: string;
  user: { id: number; email: string; full_name: string; role: string } | null;
  message_count: number;
  messages: AdminMessage[];
};

type MarketIndicator = {
  key: string;
  value: number;
  source: string;
  last_updated: string | null;
};

const TABS: Array<{ key: Tab; label: string; icon: typeof Shield }> = [
  { key: 'overview', label: 'Overview', icon: Activity },
  { key: 'conversations', label: 'Conversations', icon: MessageSquare },
  { key: 'users', label: 'Users', icon: Users },
  { key: 'tickets', label: 'Tickets', icon: TicketIcon },
  { key: 'scrapers', label: 'Scrapers and data', icon: Database },
  { key: 'marketing', label: 'Marketing Content', icon: FileText },
];

const STATUS_LABELS: Record<string, string> = {
  open: 'Open',
  in_progress: 'In progress',
  resolved: 'Resolved',
  closed: 'Closed',
};

function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-EG').format(Math.round(value));
}

export default function AdminPage() {
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [loadingData, setLoadingData] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [scraperStatus, setScraperStatus] = useState<string | null>(null);

  const [dashboard, setDashboard] = useState<AdminDashboardData | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [conversations, setConversations] = useState<AdminConversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<ConversationDetail | null>(null);
  const [indicators, setIndicators] = useState<MarketIndicator[]>([]);
  const [marketingMaterials, setMarketingMaterials] = useState<MarketingMaterial[]>([]);
  const [editingIndicator, setEditingIndicator] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');

  const [adminTickets, setAdminTickets] = useState<AdminTicket[]>([]);
  const [ticketStats, setTicketStats] = useState<TicketStats | null>(null);
  const [selectedTicket, setSelectedTicket] = useState<AdminTicketDetail | null>(null);
  const [ticketStatusFilter, setTicketStatusFilter] = useState('');
  const [ticketReplyContent, setTicketReplyContent] = useState('');
  const [ticketReplying, setTicketReplying] = useState(false);
  const [marketingGenerating, setMarketingGenerating] = useState(false);

  const [roleUpdating, setRoleUpdating] = useState<number | null>(null);
  const [blockUpdating, setBlockUpdating] = useState<number | null>(null);

  const isSuperAdmin = user?.email?.toLowerCase() === 'mustafa@osool.eg';

  const loadTabData = useCallback(async () => {
    if (authLoading || !isAuthenticated) {
      return;
    }

    setLoadingData(true);
    setLoadError(null);
    try {
      switch (activeTab) {
        case 'overview': {
          const data = await getAdminDashboard();
          setDashboard(data);
          break;
        }
        case 'conversations': {
          const data = await getAdminConversations(100);
          setConversations(data.sessions);
          break;
        }
        case 'users': {
          const data = await getAdminUsers(200);
          setUsers(data.users);
          break;
        }
        case 'tickets': {
          const [stats, list] = await Promise.all([
            getTicketStats(),
            getAdminTickets({ status: ticketStatusFilter || undefined }),
          ]);
          setTicketStats(stats);
          setAdminTickets(list.tickets);
          break;
        }
        case 'scrapers': {
          const data = await getAdminMarketIndicators();
          setIndicators((data.indicators || []) as MarketIndicator[]);
          break;
        }
        case 'marketing': {
          const data = await getMarketingMaterials();
          setMarketingMaterials(data.materials || []);
          break;
        }
      }
    } catch (error) {
      console.error(error);
      setLoadError(activeTab === 'users' ? 'Failed to load users. Please refresh or check backend logs.' : 'Failed to load admin data.');
    } finally {
      setLoadingData(false);
    }
  }, [activeTab, authLoading, isAuthenticated, ticketStatusFilter]);

  useEffect(() => {
    void loadTabData();
  }, [loadTabData]);

  const VALID_ROLES = ['investor', 'agent', 'admin', 'blocked'];

  const handleRoleChange = async (userId: number, nextRole: string) => {
    if (!VALID_ROLES.includes(nextRole)) return; // reject invalid roles
    if (roleUpdating !== null) return; // prevent concurrent updates
    setRoleUpdating(userId);
    try {
      const updated = await updateUserRole(userId, nextRole);
      setUsers((current: AdminUser[]) => current.map((entry: AdminUser) => (entry.id === userId ? { ...entry, role: updated.role } : entry)));
    } catch (error) {
      console.error(error);
      setLoadError('Failed to update role. Please try again.');
    } finally {
      setRoleUpdating(null);
    }
  };

  const handleBlockToggle = async (userId: number, blocked: boolean) => {
    if (blockUpdating !== null) return; // prevent concurrent updates
    setBlockUpdating(userId);
    try {
      await blockUser(userId, !blocked);
      setUsers((current: AdminUser[]) => current.map((entry: AdminUser) => (entry.id === userId ? { ...entry, role: blocked ? 'investor' : 'blocked' } : entry)));
    } catch (error) {
      console.error(error);
      setLoadError('Failed to update block status. Please try again.');
    } finally {
      setBlockUpdating(null);
    }
  };

  const openConversation = async (sessionId: string) => {
    setLoadingData(true);
    try {
      const detail = await getAdminConversation(sessionId);
      setSelectedConversation(detail);
    } catch (error) {
      console.error(error);
      setLoadError('Failed to load conversation.');
    } finally {
      setLoadingData(false);
    }
  };

  const openTicket = async (ticketId: number) => {
    setLoadingData(true);
    try {
      const detail = await getAdminTicketDetail(ticketId);
      setSelectedTicket(detail);
      setTicketReplyContent('');
    } catch (error) {
      console.error(error);
      setLoadError('Failed to load ticket detail.');
    } finally {
      setLoadingData(false);
    }
  };

  const handleAdminReply = async () => {
    if (!selectedTicket || !ticketReplyContent.trim() || ticketReplying) {
      return;
    }

    setTicketReplying(true);
    try {
      const reply = await addAdminTicketReply(selectedTicket.id, ticketReplyContent.trim());
      setSelectedTicket((current: AdminTicketDetail | null) => (current ? { ...current, replies: [...current.replies, reply] } : current));
      setTicketReplyContent('');
    } catch (error) {
      console.error(error);
      setLoadError('Failed to send reply. Please try again.');
    } finally {
      setTicketReplying(false);
    }
  };

  const handleTriggerScraper = async (type: 'properties' | 'economic') => {
    setScraperStatus(`Running ${type} scraper...`);
    try {
      if (type === 'properties') {
        await triggerPropertyScraper();
      } else {
        await triggerEconomicScraper();
      }
      setScraperStatus(`${type} scraper completed successfully.`);
      if (activeTab === 'scrapers') {
        await loadTabData();
      }
    } catch (error) {
      console.error(error);
      setScraperStatus(`${type} scraper failed. Check backend logs.`);
    }
    setTimeout(() => setScraperStatus(null), 5000);
  };

  const filteredConversations = useMemo(() => {
    return conversations.filter((conversation: AdminConversation) => {
      if (!searchQuery) {
        return true;
      }
      const query = searchQuery.toLowerCase();
      const email = conversation.user_email?.toLowerCase() || '';
      const name = conversation.user_name?.toLowerCase() || '';
      const preview = conversation.preview?.toLowerCase() || '';
      return email.includes(query) || name.includes(query) || preview.includes(query);
    });
  }, [conversations, searchQuery]);

  const filteredUsers = useMemo(() => {
    return users.filter((entry: AdminUser) => {
      if (!searchQuery) {
        return true;
      }
      const query = searchQuery.toLowerCase();
      return entry.email?.toLowerCase().includes(query) || entry.full_name?.toLowerCase().includes(query);
    });
  }, [users, searchQuery]);

  const overviewCards = useMemo(() => {
    if (!dashboard) {
      return [] as Array<{ label: string; value: number; icon: typeof Shield; tone: string }>;
    }
    return [
      { label: 'Total users', value: dashboard.overview.total_users, icon: Users, tone: 'text-blue-500' },
      { label: 'Total messages', value: dashboard.overview.total_messages, icon: MessageSquare, tone: 'text-emerald-500' },
      { label: 'Properties', value: dashboard.overview.total_properties, icon: Building2, tone: 'text-amber-500' },
      { label: 'Active listings', value: dashboard.overview.active_properties, icon: TrendingUp, tone: 'text-emerald-500' },
      { label: 'Chat sessions', value: dashboard.overview.total_sessions, icon: Activity, tone: 'text-cyan-500' },
      { label: 'Transactions', value: dashboard.overview.total_transactions, icon: Zap, tone: 'text-rose-500' },
      { label: 'New users (7d)', value: dashboard.recent_activity.new_users_7d, icon: UserIcon, tone: 'text-indigo-500' },
      { label: 'Messages (24h)', value: dashboard.recent_activity.messages_24h, icon: Clock3, tone: 'text-teal-500' },
    ];
  }, [dashboard]);

  const actions = (
    <button
      onClick={() => void loadTabData()}
      disabled={loadingData}
      className="inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)] disabled:opacity-60"
    >
      <RefreshCw className={`h-4 w-4 ${loadingData ? 'animate-spin' : ''}`} />
      Refresh current tab
    </button>
  );

  return (
    <AdminShell
      eyebrow="Admin operations"
      title="Run oversight, support, and data operations from one control surface."
      subtitle="This route keeps the cross-functional admin work together: overview, customer conversations, user control, support triage, and scraper operations."
      actions={actions}
    >
      {scraperStatus ? (
        <div className="rounded-[24px] border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-700 dark:text-emerald-300">
          {scraperStatus}
        </div>
      ) : null}

      {loadError ? (
        <div className="rounded-[24px] border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-500">
          {loadError}
        </div>
      ) : null}

      <section className="grid gap-6 lg:grid-cols-[0.92fr_1.08fr]">
        <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Workspace lanes</div>
          <div className="mt-4 flex flex-wrap gap-2">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.key;
              return (
                <button
                  key={tab.key}
                  type="button"
                  onClick={() => {
                    setActiveTab(tab.key);
                    setSelectedConversation(null);
                    setSelectedTicket(null);
                    setSearchQuery('');
                    setLoadError(null);
                  }}
                  className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition-colors ${
                    isActive
                      ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-300'
                      : 'border-[var(--color-border)] bg-[var(--color-background)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Link href="/admin/analytics" className="rounded-[24px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5 transition-colors hover:border-emerald-500/20">
            <div className="text-sm font-semibold text-[var(--color-text-primary)]">Analytics</div>
            <div className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">Lead intelligence and trend analysis.</div>
          </Link>
          <Link href="/admin/leads" className="rounded-[24px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5 transition-colors hover:border-emerald-500/20">
            <div className="text-sm font-semibold text-[var(--color-text-primary)]">Lead pipeline</div>
            <div className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">Stage management and buyer context.</div>
          </Link>
          <Link href="/admin/campaigns" className="rounded-[24px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5 transition-colors hover:border-emerald-500/20">
            <div className="text-sm font-semibold text-[var(--color-text-primary)]">Campaigns</div>
            <div className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">Acquisition controls and spend visibility.</div>
          </Link>
          <Link href="/admin/orchestrator" className="rounded-[24px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5 transition-colors hover:border-emerald-500/20">
            <div className="text-sm font-semibold text-[var(--color-text-primary)]">Orchestrator</div>
            <div className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">Embedded access to the orchestration admin.</div>
          </Link>
        </div>
      </section>

      {loadingData && activeTab !== 'overview' ? (
        <div className="flex items-center justify-center rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] py-16">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-500" />
        </div>
      ) : null}

      {activeTab === 'overview' ? (
        <div className="space-y-6">
          {loadingData && !dashboard ? (
            <div className="flex items-center justify-center rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] py-24">
              <Loader2 className="h-8 w-8 animate-spin text-emerald-500" />
            </div>
          ) : dashboard ? (
            <>
              <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                {overviewCards.map((card: { label: string; value: number; icon: typeof Shield; tone: string }) => {
                  const Icon = card.icon;
                  return (
                    <div key={card.label} className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                      <div className="flex items-center justify-between">
                        <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{card.label}</div>
                        <Icon className={`h-4 w-4 ${card.tone}`} />
                      </div>
                      <div className="mt-2 text-3xl font-semibold text-[var(--color-text-primary)]">{formatNumber(card.value)}</div>
                    </div>
                  );
                })}
              </section>

              <section className="grid gap-6 lg:grid-cols-[1fr_0.92fr]">
                <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
                  <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Admin focus</div>
                  <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[var(--color-text-primary)]">The main operating areas</h2>
                  <div className="mt-6 grid gap-3 sm:grid-cols-2">
                    <button type="button" onClick={() => setActiveTab('conversations')} className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4 text-left">
                      <div className="text-sm font-semibold text-[var(--color-text-primary)]">Conversations</div>
                      <div className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">Inspect chat threads and escalation context.</div>
                    </button>
                    <button type="button" onClick={() => setActiveTab('users')} className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4 text-left">
                      <div className="text-sm font-semibold text-[var(--color-text-primary)]">Users</div>
                      <div className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">Control roles, status, and account exposure.</div>
                    </button>
                    <button type="button" onClick={() => setActiveTab('tickets')} className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4 text-left">
                      <div className="text-sm font-semibold text-[var(--color-text-primary)]">Tickets</div>
                      <div className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">Manage support queue and reply from admin.</div>
                    </button>
                    <button type="button" onClick={() => setActiveTab('scrapers')} className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4 text-left">
                      <div className="text-sm font-semibold text-[var(--color-text-primary)]">Scrapers</div>
                      <div className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">Trigger ingestion and review market indicators.</div>
                    </button>
                  </div>
                </div>

                <div className="rounded-[32px] border border-[var(--color-border)] bg-emerald-500/10 p-6">
                  <div className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700 dark:text-emerald-300">Admin note</div>
                  <h2 className="mt-3 text-2xl font-semibold tracking-tight text-[var(--color-text-primary)]">Keep the operating layer readable.</h2>
                  <div className="mt-4 space-y-3 text-sm leading-6 text-[var(--color-text-secondary)]">
                    <p>Use this page for fast supervision, then move into the dedicated subpages when deeper work is required.</p>
                    <p>Conversations and tickets should stay factual and auditable. User roles should stay minimal and intentional.</p>
                    <p>Scraper triggers should be used for known refresh needs, not as a substitute for fixing data pipelines.</p>
                  </div>
                </div>
              </section>
            </>
          ) : null}
        </div>
      ) : null}

      {activeTab === 'conversations' ? (
        <section className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
          {!selectedConversation ? (
            <>
              <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6 lg:col-span-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-text-muted)]" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(event) => setSearchQuery(event.target.value)}
                    placeholder="Search by user name, email, or message preview"
                    className="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] py-3 pl-10 pr-4 text-sm text-[var(--color-text-primary)] outline-none"
                  />
                </div>
                <div className="mt-6 space-y-3">
                  {filteredConversations.map((conversation: AdminConversation) => (
                    <button
                      key={conversation.session_id}
                      type="button"
                      onClick={() => void openConversation(conversation.session_id)}
                      className="w-full rounded-[24px] border border-[var(--color-border)] bg-[var(--color-background)] p-5 text-left transition-colors hover:border-emerald-500/20"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-sm font-semibold text-[var(--color-text-primary)]">{conversation.user_name || conversation.user_email || 'Anonymous'}</span>
                            {conversation.user_email ? <span className="text-xs text-[var(--color-text-muted)]">{conversation.user_email}</span> : null}
                          </div>
                          {conversation.preview ? <p className="mt-2 line-clamp-2 text-sm leading-6 text-[var(--color-text-secondary)]">{conversation.preview}</p> : null}
                          <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-[var(--color-text-muted)]">
                            <span>{conversation.message_count} messages</span>
                            <span>{conversation.last_message_at ? new Date(conversation.last_message_at).toLocaleString() : 'No activity'}</span>
                          </div>
                        </div>
                        <ChevronRight className="mt-1 h-4 w-4 text-[var(--color-text-muted)]" />
                      </div>
                    </button>
                  ))}
                  {!filteredConversations.length && !loadingData ? (
                    <div className="rounded-[24px] border border-dashed border-[var(--color-border)] bg-[var(--color-background)] p-8 text-center text-sm text-[var(--color-text-secondary)]">
                      No conversations found.
                    </div>
                  ) : null}
                </div>
              </div>
            </>
          ) : (
            <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6 lg:col-span-2">
              <button
                type="button"
                onClick={() => setSelectedConversation(null)}
                className="inline-flex items-center gap-2 text-sm font-medium text-[var(--color-text-secondary)] transition-colors hover:text-[var(--color-text-primary)]"
              >
                <ArrowLeft className="h-4 w-4" />
                Back to conversations
              </button>
              {selectedConversation.user ? (
                <div className="mt-6 rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                  <div className="text-sm font-semibold text-[var(--color-text-primary)]">{selectedConversation.user.full_name}</div>
                  <div className="mt-1 text-sm text-[var(--color-text-secondary)]">{selectedConversation.user.email}</div>
                </div>
              ) : null}
              <div className="mt-6 space-y-3">
                {(selectedConversation.messages || []).map((message: AdminMessage) => (
                  <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[82%] rounded-[24px] px-4 py-3 ${message.role === 'user' ? 'bg-[var(--color-text-primary)] text-[var(--color-background)]' : 'border border-[var(--color-border)] bg-[var(--color-background)] text-[var(--color-text-primary)]'}`}>
                      <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase opacity-70">
                        {message.role === 'user' ? <UserIcon className="h-3 w-3" /> : <Bot className="h-3 w-3 text-emerald-500" />}
                        <span>{message.role === 'user' ? 'Customer' : 'Osool'}</span>
                        <span className="ml-auto">{message.created_at ? new Date(message.created_at).toLocaleTimeString() : ''}</span>
                      </div>
                      <p className="whitespace-pre-wrap text-sm leading-6">{message.content}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      ) : null}

      {activeTab === 'users' ? (
        <section className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-text-muted)]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search users"
              className="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] py-3 pl-10 pr-4 text-sm text-[var(--color-text-primary)] outline-none"
            />
          </div>
          <div className="mt-6 overflow-x-auto rounded-2xl border border-[var(--color-border)]">
            <table className="w-full text-left text-sm">
              <thead className="bg-[var(--color-background)]">
                <tr>
                  <th className="px-3 py-3 font-medium">User</th>
                  <th className="px-3 py-3 font-medium">Role</th>
                  <th className="px-3 py-3 font-medium">Messages</th>
                  <th className="px-3 py-3 font-medium">KYC</th>
                  <th className="px-3 py-3 font-medium">Joined</th>
                  <th className="px-3 py-3 font-medium">Last active</th>
                  {isSuperAdmin ? <th className="px-3 py-3 font-medium">Actions</th> : null}
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map((entry: AdminUser) => {
                  const isCoreAdmin = entry.email === 'mustafa@osool.eg' || entry.email === 'hani@osool.eg';
                  const isBlocked = entry.role === 'blocked';
                  return (
                    <tr key={entry.id} className={`border-t border-[var(--color-border)] ${isBlocked ? 'opacity-60' : ''}`}>
                      <td className="px-3 py-3">
                        <div className="font-medium text-[var(--color-text-primary)]">{entry.full_name || '-'}</div>
                        <div className="mt-1 text-xs text-[var(--color-text-muted)]">{entry.email}</div>
                      </td>
                      <td className="px-3 py-3">
                        {isCoreAdmin ? (
                          <span className="rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-600 dark:text-emerald-300">admin</span>
                        ) : isSuperAdmin ? (
                          <select
                            title="Change user role"
                            value={entry.role}
                            disabled={roleUpdating === entry.id}
                            onChange={(event) => void handleRoleChange(entry.id, event.target.value)}
                            className="rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-2.5 py-1 text-xs font-semibold text-[var(--color-text-primary)]"
                          >
                            <option value="investor">investor</option>
                            <option value="agent">agent</option>
                            <option value="analyst">analyst</option>
                            <option value="admin">admin</option>
                            <option value="blocked">blocked</option>
                          </select>
                        ) : (
                          <span className="rounded-full bg-blue-500/10 px-2.5 py-1 text-xs font-semibold text-blue-600 dark:text-blue-300">{entry.role}</span>
                        )}
                      </td>
                      <td className="px-3 py-3 text-[var(--color-text-secondary)]">{entry.message_count}</td>
                      <td className="px-3 py-3">
                        <span className={`text-xs font-semibold ${entry.kyc_status === 'verified' ? 'text-emerald-600 dark:text-emerald-300' : 'text-amber-600 dark:text-amber-300'}`}>{entry.kyc_status}</span>
                      </td>
                      <td className="px-3 py-3 text-xs text-[var(--color-text-muted)]">{entry.created_at ? new Date(entry.created_at).toLocaleDateString() : '-'}</td>
                      <td className="px-3 py-3 text-xs text-[var(--color-text-muted)]">{entry.last_activity ? new Date(entry.last_activity).toLocaleDateString() : 'Never'}</td>
                      {isSuperAdmin ? (
                        <td className="px-3 py-3">
                          {!isCoreAdmin ? (
                            <button
                              type="button"
                              disabled={blockUpdating === entry.id}
                              onClick={() => void handleBlockToggle(entry.id, isBlocked)}
                              className={`rounded-full border px-3 py-1 text-xs font-semibold ${isBlocked ? 'border-emerald-500/30 text-emerald-600 dark:text-emerald-300' : 'border-red-500/30 text-red-500'}`}
                            >
                              {blockUpdating === entry.id ? '...' : isBlocked ? 'Unblock' : 'Block'}
                            </button>
                          ) : null}
                        </td>
                      ) : null}
                    </tr>
                  );
                })}
                {!filteredUsers.length && !loadingData ? (
                  <tr>
                    <td colSpan={isSuperAdmin ? 7 : 6} className="px-3 py-10 text-center text-sm text-[var(--color-text-secondary)]">
                      No users found.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {activeTab === 'tickets' ? (
        <section className="space-y-6">
          {!selectedTicket && ticketStats ? (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
              <StatusCard label="Open" value={ticketStats.open} tone="text-blue-500" />
              <StatusCard label="In progress" value={ticketStats.in_progress} tone="text-amber-500" />
              <StatusCard label="Resolved" value={ticketStats.resolved} tone="text-emerald-500" />
              <StatusCard label="Closed" value={ticketStats.closed} tone="text-[var(--color-text-muted)]" />
              <StatusCard label="Total" value={ticketStats.total} tone="text-[var(--color-text-primary)]" />
            </div>
          ) : null}

          {selectedTicket ? (
            <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
              <button
                type="button"
                onClick={() => setSelectedTicket(null)}
                className="inline-flex items-center gap-2 text-sm font-medium text-[var(--color-text-secondary)] transition-colors hover:text-[var(--color-text-primary)]"
              >
                <ArrowLeft className="h-4 w-4" />
                Back to tickets
              </button>
              <div className="mt-6 rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-5">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <div className="text-lg font-semibold text-[var(--color-text-primary)]">{selectedTicket.subject}</div>
                    <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-[var(--color-text-muted)]">
                      <span>#{selectedTicket.id}</span>
                      <span>{selectedTicket.user?.name} ({selectedTicket.user?.email})</span>
                      <span>{selectedTicket.category}</span>
                      <span>{selectedTicket.priority}</span>
                    </div>
                  </div>
                  <select
                    title="Change ticket status"
                    value={selectedTicket.status}
                    onChange={async (event) => {
                      const nextStatus = event.target.value;
                      try {
                        await updateTicketStatus(selectedTicket.id, nextStatus);
                        setSelectedTicket((current: AdminTicketDetail | null) => (current ? { ...current, status: nextStatus } : current));
                        setAdminTickets((current: AdminTicket[]) => current.map((entry: AdminTicket) => (entry.id === selectedTicket.id ? { ...entry, status: nextStatus } : entry)));
                      } catch (error) {
                        console.error(error);
                      }
                    }}
                    className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text-primary)]"
                  >
                    <option value="open">Open</option>
                    <option value="in_progress">In progress</option>
                    <option value="resolved">Resolved</option>
                    <option value="closed">Closed</option>
                  </select>
                </div>
                <div className="mt-4 whitespace-pre-wrap text-sm leading-6 text-[var(--color-text-secondary)]">{selectedTicket.description}</div>
              </div>

              <div className="mt-6 space-y-3">
                {(selectedTicket.replies || []).map((reply) => (
                  <div key={reply.id} className={`rounded-[24px] border p-4 ${reply.is_admin_reply ? 'border-emerald-500/20 bg-emerald-500/5' : 'border-[var(--color-border)] bg-[var(--color-background)]'}`}>
                    <div className="flex items-center gap-2 text-xs">
                      <span className={`font-semibold ${reply.is_admin_reply ? 'text-emerald-600 dark:text-emerald-300' : 'text-[var(--color-text-primary)]'}`}>
                        {reply.user_name} {reply.is_admin_reply ? '(Admin)' : ''}
                      </span>
                      <span className="text-[var(--color-text-muted)]">{reply.created_at ? new Date(reply.created_at).toLocaleString() : ''}</span>
                    </div>
                    <div className="mt-2 whitespace-pre-wrap text-sm leading-6 text-[var(--color-text-secondary)]">{reply.content}</div>
                  </div>
                ))}
              </div>

              <div className="mt-6 flex gap-2">
                <input
                  type="text"
                  value={ticketReplyContent}
                  onChange={(event) => setTicketReplyContent(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' && !event.shiftKey && ticketReplyContent.trim()) {
                      event.preventDefault();
                      void handleAdminReply();
                    }
                  }}
                  placeholder="Reply as admin"
                  className="flex-1 rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text-primary)] outline-none"
                />
                <button
                  type="button"
                  onClick={() => void handleAdminReply()}
                  disabled={!ticketReplyContent.trim() || ticketReplying}
                  className="inline-flex items-center gap-2 rounded-2xl bg-[var(--color-text-primary)] px-4 py-3 text-sm font-semibold text-[var(--color-background)] disabled:opacity-60"
                >
                  {ticketReplying ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  Reply
                </button>
              </div>
            </div>
          ) : (
            <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
              <div className="flex flex-wrap gap-2">
                {[
                  { key: '', label: 'All' },
                  { key: 'open', label: 'Open' },
                  { key: 'in_progress', label: 'In progress' },
                  { key: 'resolved', label: 'Resolved' },
                  { key: 'closed', label: 'Closed' },
                ].map((filter) => (
                  <button
                    key={filter.key || 'all'}
                    type="button"
                    onClick={() => setTicketStatusFilter(filter.key)}
                    className={`rounded-full border px-4 py-2 text-sm font-medium ${ticketStatusFilter === filter.key ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-300' : 'border-[var(--color-border)] bg-[var(--color-background)] text-[var(--color-text-secondary)]'}`}
                  >
                    {filter.label}
                  </button>
                ))}
              </div>
              <div className="mt-6 overflow-x-auto rounded-2xl border border-[var(--color-border)]">
                <table className="w-full text-left text-sm">
                  <thead className="bg-[var(--color-background)]">
                    <tr>
                      <th className="px-3 py-3 font-medium">ID</th>
                      <th className="px-3 py-3 font-medium">Subject</th>
                      <th className="px-3 py-3 font-medium">User</th>
                      <th className="px-3 py-3 font-medium">Category</th>
                      <th className="px-3 py-3 font-medium">Priority</th>
                      <th className="px-3 py-3 font-medium">Status</th>
                      <th className="px-3 py-3 font-medium">Replies</th>
                      <th className="px-3 py-3 font-medium">Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {adminTickets.map((ticket: AdminTicket) => (
                      <tr key={ticket.id} onClick={() => void openTicket(ticket.id)} className="cursor-pointer border-t border-[var(--color-border)] transition-colors hover:bg-[var(--color-background)]">
                        <td className="px-3 py-3 text-xs text-[var(--color-text-muted)]">#{ticket.id}</td>
                        <td className="px-3 py-3 font-medium text-[var(--color-text-primary)]">{ticket.subject}</td>
                        <td className="px-3 py-3">
                          <div className="text-xs text-[var(--color-text-primary)]">{ticket.user_name}</div>
                          <div className="mt-1 text-[11px] text-[var(--color-text-muted)]">{ticket.user_email}</div>
                        </td>
                        <td className="px-3 py-3 text-xs text-[var(--color-text-secondary)]">{ticket.category}</td>
                        <td className="px-3 py-3 text-xs text-[var(--color-text-secondary)]">{ticket.priority}</td>
                        <td className="px-3 py-3">
                          <span className="rounded-full bg-[var(--color-background)] px-2.5 py-1 text-xs font-semibold text-[var(--color-text-primary)]">{STATUS_LABELS[ticket.status] || ticket.status}</span>
                        </td>
                        <td className="px-3 py-3 text-xs text-[var(--color-text-muted)]">{ticket.replies_count}</td>
                        <td className="px-3 py-3 text-xs text-[var(--color-text-muted)]">{ticket.created_at ? new Date(ticket.created_at).toLocaleDateString() : '-'}</td>
                      </tr>
                    ))}
                    {!adminTickets.length && !loadingData ? (
                      <tr>
                        <td colSpan={8} className="px-3 py-10 text-center text-sm text-[var(--color-text-secondary)]">No tickets found.</td>
                      </tr>
                    ) : null}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </section>
      ) : null}

      {activeTab === 'scrapers' ? (
        <div className="space-y-6">
          <section className="grid gap-4 md:grid-cols-2">
            <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
              <div className="flex items-center gap-2 text-sm font-semibold text-[var(--color-text-primary)]">
                <Building2 className="h-5 w-5 text-emerald-500" />
                Property scraper
              </div>
              <p className="mt-3 text-sm leading-6 text-[var(--color-text-secondary)]">Scrapes Nawy for refreshed property inventory and runs on a scheduled cadence outside this control surface.</p>
              <button type="button" onClick={() => void handleTriggerScraper('properties')} className="mt-5 rounded-full bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)]">
                Run property scraper
              </button>
            </div>
            <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
              <div className="flex items-center gap-2 text-sm font-semibold text-[var(--color-text-primary)]">
                <TrendingUp className="h-5 w-5 text-amber-500" />
                Economic scraper
              </div>
              <p className="mt-3 text-sm leading-6 text-[var(--color-text-secondary)]">Fetches exchange rate, inflation, gold, and banking indicators used in market interpretation layers.</p>
              <button type="button" onClick={() => void handleTriggerScraper('economic')} className="mt-5 rounded-full bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)]">
                Run economic scraper
              </button>
            </div>
          </section>

          <section className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Market indicators</div>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[var(--color-text-primary)]">Current data snapshot</h2>
            {indicators.length ? (
              <div className="mt-6 overflow-x-auto rounded-2xl border border-[var(--color-border)]">
                <table className="w-full text-left text-sm">
                  <thead className="bg-[var(--color-background)]">
                    <tr>
                      <th className="px-3 py-3 font-medium">Indicator</th>
                      <th className="px-3 py-3 font-medium">Value</th>
                      <th className="px-3 py-3 font-medium">Source</th>
                      <th className="px-3 py-3 font-medium">Updated</th>
                      <th className="px-3 py-3 font-medium w-20"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {indicators.map((indicator: MarketIndicator) => (
                      <tr key={indicator.key} className="border-t border-[var(--color-border)]">
                        <td className="px-3 py-3 font-medium text-[var(--color-text-primary)]">{indicator.key.replace(/_/g, ' ')}</td>
                        <td className="px-3 py-3 font-mono text-[var(--color-text-primary)]">
                          {editingIndicator === indicator.key ? (
                            <input
                              type="number"
                              step="any"
                              value={editValue}
                              onChange={(e) => setEditValue(e.target.value)}
                              onKeyDown={async (e) => {
                                if (e.key === 'Enter') {
                                  const numVal = parseFloat(editValue);
                                  if (!isNaN(numVal)) {
                                    try {
                                      await updateAdminMarketIndicator(indicator.key, numVal);
                                      setIndicators(prev => prev.map(ind => ind.key === indicator.key ? { ...ind, value: numVal, source: 'Admin Override', last_updated: new Date().toISOString() } : ind));
                                    } catch { /* ignore */ }
                                  }
                                  setEditingIndicator(null);
                                } else if (e.key === 'Escape') {
                                  setEditingIndicator(null);
                                }
                              }}
                              className="w-28 rounded border border-[var(--color-border)] bg-[var(--color-background)] px-2 py-1 text-sm font-mono"
                              autoFocus
                            />
                          ) : (
                            indicator.value < 1 ? `${(indicator.value * 100).toFixed(1)}%` : indicator.value.toLocaleString()
                          )}
                        </td>
                        <td className="px-3 py-3 text-xs text-[var(--color-text-muted)]">{indicator.source}</td>
                        <td className="px-3 py-3 text-xs text-[var(--color-text-muted)]">{indicator.last_updated ? new Date(indicator.last_updated).toLocaleDateString() : '-'}</td>
                        <td className="px-3 py-3">
                          <button
                            type="button"
                            onClick={() => { setEditingIndicator(indicator.key); setEditValue(String(indicator.value)); }}
                            className="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] underline"
                          >
                            Edit
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="mt-6 rounded-[24px] border border-dashed border-[var(--color-border)] bg-[var(--color-background)] p-8 text-center text-sm text-[var(--color-text-secondary)]">
                No indicators are available.
              </div>
            )}
          </section>
        </div>
      ) : null}

      {activeTab === 'marketing' ? (
        <div className="space-y-6">
          <header className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold tracking-tight">Marketing Answers</h2>
              <p className="mt-1 text-sm text-[var(--color-text-secondary)]">AI-generated answers for marketing & social media.</p>
            </div>
            <button
              onClick={async () => {
                if (marketingGenerating) {
                  return;
                }

                setMarketingGenerating(true);
                try {
                  await generateMarketingMaterials();
                  setLoadError(null);
                  await loadTabData();
                } catch (error) {
                  console.error(error);
                  setLoadError('Failed to start marketing content generation.');
                } finally {
                  setMarketingGenerating(false);
                }
              }}
              disabled={marketingGenerating}
              className="inline-flex items-center gap-2 rounded-full bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-60"
            >
              {marketingGenerating ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
              {marketingGenerating ? 'Refreshing…' : 'Regenerate Content'}
            </button>
          </header>

          <section className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6 md:p-8">
            {marketingMaterials.length > 0 ? (
              <div className="space-y-6">
                {marketingMaterials.map((mat) => (
                  <div key={mat.id} className="rounded-2xl border border-[var(--color-border)] p-4 bg-[var(--color-background)]">
                    <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--color-primary)]">
                      {mat.category}
                    </div>
                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <div className="font-medium text-sm text-[var(--color-text-secondary)]">Question (EN)</div>
                        <p className="mb-2">{mat.question_en}</p>
                        <div className="font-medium text-sm text-[var(--color-text-secondary)]">Answer (EN)</div>
                        <p className="text-sm whitespace-pre-wrap">{mat.answer_en || 'Not generated yet'}</p>
                      </div>
                      <div dir="rtl">
                        <div className="font-medium text-sm text-[var(--color-text-secondary)]">السؤال</div>
                        <p className="mb-2">{mat.question_ar}</p>
                        <div className="font-medium text-sm text-[var(--color-text-secondary)]">الإجابة</div>
                        <p className="text-sm whitespace-pre-wrap">{mat.answer_ar || 'لم يتم الإنشاء بعد'}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="mt-6 rounded-[24px] border border-dashed border-[var(--color-border)] bg-[var(--color-background)] p-8 text-center text-sm text-[var(--color-text-secondary)]">
                No marketing materials available. Please seed the database.
              </div>
            )}
          </section>
        </div>
      ) : null}

    </AdminShell>
  );
}

function StatusCard({ label, value, tone }: { label: string; value: number; tone: string }) {
  return (
    <div className="rounded-[24px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{label}</div>
      <div className={`mt-2 text-3xl font-semibold ${tone}`}>{value}</div>
    </div>
  );
}
