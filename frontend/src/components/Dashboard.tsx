/**
 * Observability Dashboard - Admin UI with Left Sidebar
 */

import { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BookOpen,
  Wrench,
  Users,
  Terminal,
  Cpu,
  FileText,
  ChevronLeft,
  ChevronRight,
  HelpCircle,
} from 'lucide-react';
import { apiClient, type UserSummary } from '../services/api';
import { StoryBeatTool } from './StoryBeatTool';
import { ToolsView } from './tools/ToolsView';
import UserTestingTool from './UserTestingTool';
import { ToolCallsTool } from './ToolCallsTool';
import { CharacterTool } from './CharacterTool';
import { SystemLogTool } from './SystemLogTool';
import { KeyboardShortcutsModal } from './KeyboardShortcutsModal';
import { LoadingSpinner } from './LoadingSpinner';
import { ThemeToggle } from './ThemeToggle';
import { Button } from '@/components/ui/button';
import { Select } from '@/components/ui/select';

import { cn } from '@/lib/utils';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import './LoadingSpinner.css';

type View = 'home' | 'story' | 'tools' | 'users' | 'toolcalls' | 'characters';

const NAV_ITEMS: { id: View; label: string; icon: React.ReactNode; shortcut: string }[] = [
  { id: 'home',       label: 'Logs',         icon: <Terminal className="h-4 w-4" />,  shortcut: '1' },
  { id: 'story',      label: 'Story Beats',  icon: <BookOpen className="h-4 w-4" />,  shortcut: '2' },
  { id: 'tools',      label: 'Tools',        icon: <Wrench className="h-4 w-4" />,    shortcut: '3' },
  { id: 'users',      label: 'User Testing', icon: <Users className="h-4 w-4" />,     shortcut: '4' },
  { id: 'toolcalls',  label: 'Tool Calls',   icon: <FileText className="h-4 w-4" />,  shortcut: '5' },
  { id: 'characters', label: 'Characters',   icon: <Cpu className="h-4 w-4" />,       shortcut: '6' },
];

function ViewContent({ view, userId }: { view: View; userId: string }) {
  switch (view) {
    case 'story':      return <StoryBeatTool userId={userId} />;
    case 'tools':      return <ToolsView userId={userId} />;
    case 'users':      return <UserTestingTool />;
    case 'toolcalls':  return <ToolCallsTool userId={userId} />;
    case 'characters': return <CharacterTool userId={userId} />;
    default:           return <SystemLogTool />;
  }
}

export function Dashboard() {
  const [currentView, setCurrentView] = useState<View>('home');
  const [selectedUserId, setSelectedUserId] = useState<string>('');
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const userSelectRef = useRef<HTMLSelectElement>(null);

  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.health(),
  });

  const { data: users, isLoading: usersLoading, error } = useQuery({
    queryKey: ['users'],
    queryFn: () => apiClient.listUsers(),
  });

  // Keyboard shortcuts
  useKeyboardShortcuts([
    { key: '1', handler: () => setCurrentView('home'),       description: 'Go to Logs' },
    { key: '2', handler: () => setCurrentView('story'),      description: 'Go to Story Beats' },
    { key: '3', handler: () => setCurrentView('tools'),      description: 'Go to Tools' },
    { key: '4', handler: () => setCurrentView('users'),      description: 'Go to User Testing' },
    { key: '5', handler: () => setCurrentView('toolcalls'),  description: 'Go to Tool Calls' },
    { key: '6', handler: () => setCurrentView('characters'), description: 'Go to Characters' },
    { key: 'u', ctrl: true, handler: () => userSelectRef.current?.focus(), description: 'Focus user selector' },
    { key: '?', shift: true, handler: () => setShowShortcuts(true), description: 'Show shortcuts' },
  ]);

  // Auto-select first user
  useEffect(() => {
    if (!selectedUserId && users && users.length > 0) {
      const userJustin = users.find((u: UserSummary) => u.user_id === 'user_justin');
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSelectedUserId(userJustin?.user_id || users[0].user_id);
    }
  }, [users, selectedUserId]);

  if (healthLoading || usersLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[hsl(var(--background))]">
        <LoadingSpinner text="Loading dashboard..." size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center bg-[hsl(var(--background))] p-8">
        <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-8 text-center max-w-md">
          <h2 className="text-xl font-semibold text-red-500 mb-2">Connection Error</h2>
          <p className="text-[hsl(var(--muted-foreground))]">Unable to connect to API. Make sure the backend is running.</p>
          <p className="mt-3 rounded bg-[hsl(var(--muted))] p-3 font-mono text-xs text-[hsl(var(--muted-foreground))]">
            {String(error)}
          </p>
        </div>
      </div>
    );
  }

  const currentNavItem = NAV_ITEMS.find(n => n.id === currentView);

  return (
    <div className="flex h-screen bg-[hsl(var(--background))] text-[hsl(var(--foreground))]">
      {/* ── Left Sidebar ── */}
      <aside
        className={cn(
          'flex flex-col border-r border-[hsl(var(--border))] bg-[hsl(var(--sidebar-background))] transition-all duration-200',
          sidebarCollapsed ? 'w-16' : 'w-56'
        )}
      >
        {/* Logo / Brand */}
        <div className="flex h-14 items-center justify-between px-4 border-b border-[hsl(var(--border))]">
          {!sidebarCollapsed && (
            <span className="font-semibold text-sm text-[hsl(var(--sidebar-foreground))] truncate">
              Aperture Assist
            </span>
          )}
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 shrink-0"
            onClick={() => setSidebarCollapsed(c => !c)}
            title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {sidebarCollapsed
              ? <ChevronRight className="h-4 w-4" />
              : <ChevronLeft className="h-4 w-4" />}
          </Button>
        </div>

        {/* Nav Items */}
        <nav className="flex-1 py-3 space-y-1 px-2">
          {NAV_ITEMS.map(item => (
            <button
              key={item.id}
              onClick={() => setCurrentView(item.id)}
              title={sidebarCollapsed ? `${item.label} (${item.shortcut})` : undefined}
              className={cn(
                'flex w-full items-center gap-3 rounded-md px-2 py-2 text-sm font-medium transition-colors',
                currentView === item.id
                  ? 'bg-[hsl(var(--sidebar-primary))] text-[hsl(var(--sidebar-primary-foreground))]'
                  : 'text-[hsl(var(--sidebar-foreground))] hover:bg-[hsl(var(--sidebar-accent))] hover:text-[hsl(var(--sidebar-accent-foreground))]'
              )}
            >
              {item.icon}
              {!sidebarCollapsed && (
                <>
                  <span className="flex-1 truncate">{item.label}</span>
                  <kbd className="ml-auto text-xs opacity-50">{item.shortcut}</kbd>
                </>
              )}
            </button>
          ))}
        </nav>

        {/* Sidebar Footer */}
        <div className="border-t border-[hsl(var(--border))] p-3 space-y-2">
          {!sidebarCollapsed && users && users.length > 0 && (
            <div className="space-y-1">
              <label className="text-xs text-[hsl(var(--muted-foreground))] font-medium">User</label>
              <Select
                ref={userSelectRef}
                value={selectedUserId}
                onChange={(e) => setSelectedUserId(e.target.value)}
                className="text-xs h-8"
              >
                {users?.map((user: UserSummary) => (
                  <option key={user.user_id} value={user.user_id}>
                    {user.user_id}{user.user_id === 'user_justin' ? ' (Prod)' : ''}
                  </option>
                ))}
              </Select>
            </div>
          )}
        </div>
      </aside>

      {/* ── Main Content ── */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Header Bar */}
        <header className="flex h-14 items-center justify-between border-b border-[hsl(var(--border))] bg-[hsl(var(--background))] px-6">
          <div className="flex items-center gap-3">
            {currentNavItem && (
              <>
                <span className="text-[hsl(var(--muted-foreground))]">{currentNavItem.icon}</span>
                <h1 className="text-lg font-semibold">{currentNavItem.label}</h1>
              </>
            )}
          </div>

          <div className="flex items-center gap-3">
            {/* Health Status */}
            <div className="flex items-center gap-2 rounded-md border border-[hsl(var(--border))] px-3 py-1.5 text-sm">
              <span
                className={cn(
                  'h-2 w-2 rounded-full',
                  health?.status === 'ok' ? 'bg-green-500 shadow-[0_0_6px_#22c55e]' : 'bg-red-500 shadow-[0_0_6px_#ef4444]'
                )}
              />
              <span className="text-[hsl(var(--muted-foreground))] text-xs">
                {health?.status === 'ok' ? 'Connected' : 'Error'}
              </span>
            </div>

            <ThemeToggle />

            <Button
              variant="ghost"
              size="icon"
              onClick={() => setShowShortcuts(true)}
              title="Keyboard shortcuts (Shift+?)"
            >
              <HelpCircle className="h-4 w-4" />
            </Button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto">
          <ViewContent view={currentView} userId={selectedUserId} />
        </main>

        {/* Footer */}
        <footer className="flex items-center gap-3 border-t border-[hsl(var(--border))] px-6 py-2 text-xs text-[hsl(var(--muted-foreground))]">
          <span>v{health?.version} • {new Date(health?.timestamp || '').toLocaleTimeString()}</span>
          <span aria-hidden="true">·</span>
          <span>Press <kbd className="rounded bg-[hsl(var(--muted))] border border-[hsl(var(--border))] px-1 py-0.5 font-mono text-xs">?</kbd> for shortcuts</span>
        </footer>
      </div>

      <KeyboardShortcutsModal
        isOpen={showShortcuts}
        onClose={() => setShowShortcuts(false)}
      />
    </div>
  );
}
