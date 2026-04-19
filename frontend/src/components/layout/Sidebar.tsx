// src/components/layout/Sidebar.tsx
"use client";

/**
 * Sidebar — navigazione principale.
 *
 * Desktop: sidebar fissa w-64. Mobile: Sheet via hamburger.
 *
 * Pattern collapsible: voce principale cliccabile (naviga)
 * + sotto-pagine a scomparsa. Click ovunque sulla riga = naviga.
 * Chevron integrato nel link per toggle expand/collapse.
 * Auto-expand se la route corrente matcha un sub-item.
 *
 * Bottom zone: Guida e Impostazioni con trattamento secondario
 * (testo piu' piccolo, icone muted, nessun hover bg prominente).
 */

import { useState, useCallback, useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Calendar,
  Users,
  FileText,
  Wallet,
  BookOpen,
  Settings,
  LogOut,
  Dumbbell,
  ClipboardList,
  Activity,
  BarChart3,
  Search,
  SunMedium,
  HandCoins,
  MessageCircle,
  Moon,
  Sun,
  ChevronRight,
} from "lucide-react";

import { useTheme } from "next-themes";
import { LogoIcon } from "@/components/ui/logo";
import { cn } from "@/lib/utils";
import { getStoredTrainer, logout } from "@/lib/auth";
import { clearPageState } from "@/lib/url-state";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

// ════════════════════════════════════════════════════════════
// TYPES
// ════════════════════════════════════════════════════════════

type NavLink = {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  guideId?: string;
  activeMatch?: (pathname: string) => boolean;
};

type NavGroup = { main: NavLink; children: NavLink[] };
type NavEntry = NavLink | NavGroup;

function isGroup(entry: NavEntry): entry is NavGroup {
  return "main" in entry;
}

// ════════════════════════════════════════════════════════════
// DATA
// ════════════════════════════════════════════════════════════

const NAV_TOP: NavEntry[] = [
  { href: "/oggi", label: "Oggi", icon: SunMedium },
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/agenda", label: "Agenda", icon: Calendar },
  {
    main: {
      href: "/clienti",
      label: "Clienti",
      icon: Users,
      guideId: "sidebar-clienti",
      activeMatch: (p) => p === "/clienti" || /^\/clienti\/\d+(\/|$)/.test(p),
    },
    children: [
      { href: "/monitoraggio", label: "Monitoraggio", icon: BarChart3, activeMatch: (p) => p.startsWith("/monitoraggio") },
      { href: "/comunicazioni", label: "Comunicazioni", icon: MessageCircle },
    ],
  },
  {
    main: { href: "/contratti", label: "Contratti", icon: FileText },
    children: [
      { href: "/rinnovi-incassi", label: "Rinnovi & Incassi", icon: HandCoins },
      { href: "/cassa", label: "Cassa", icon: Wallet },
    ],
  },
  {
    main: { href: "/schede", label: "Schede", icon: ClipboardList, guideId: "sidebar-schede" },
    children: [
      { href: "/esercizi", label: "Esercizi", icon: Dumbbell },
      { href: "/allenamenti", label: "Aderenza", icon: Activity },
    ],
  },
];

const NAV_BOTTOM: NavLink[] = [
  { href: "/guida", label: "Guida", icon: BookOpen, guideId: "sidebar-guida" },
  { href: "/impostazioni", label: "Impostazioni", icon: Settings },
];

// ════════════════════════════════════════════════════════════
// HELPERS
// ════════════════════════════════════════════════════════════

function isLinkActive(item: NavLink, pathname: string): boolean {
  if (item.activeMatch) return item.activeMatch(pathname);
  if (item.href === "/") return pathname === "/";
  return pathname.startsWith(item.href);
}

function isGroupActive(group: NavGroup, pathname: string): boolean {
  return isLinkActive(group.main, pathname) || group.children.some((c) => isLinkActive(c, pathname));
}

// ════════════════════════════════════════════════════════════
// NAV ITEM — singolo link
// ════════════════════════════════════════════════════════════

function NavItem({
  item,
  pathname,
  onNavigate,
  showPulse,
  indent,
}: {
  item: NavLink;
  pathname: string;
  onNavigate?: () => void;
  showPulse?: boolean;
  indent?: boolean;
}) {
  const active = isLinkActive(item, pathname);

  return (
    <Link
      href={item.href}
      onClick={() => { clearPageState(item.href); onNavigate?.(); }}
      data-guide={item.guideId}
      className={cn(
        "relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-150",
        indent && "ml-4 py-1.5",
        active
          ? "bg-primary/10 text-primary font-semibold before:absolute before:inset-y-[6px] before:left-0 before:w-[3px] before:rounded-full before:bg-primary before:content-['']"
          : indent
            ? "text-muted-foreground hover:text-foreground hover:bg-accent/50"
            : "text-muted-foreground hover:bg-accent/70 hover:text-foreground"
      )}
    >
      <item.icon className={cn("shrink-0", indent ? "h-3.5 w-3.5" : "h-4.5 w-4.5")} />
      <span className={indent ? "text-[13px]" : ""}>{item.label}</span>
      {showPulse && (
        <span className="absolute right-2 top-1/2 -translate-y-1/2">
          <span className="absolute inline-flex h-2 w-2 animate-ping rounded-full bg-primary opacity-75" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-primary" />
        </span>
      )}
    </Link>
  );
}

// ════════════════════════════════════════════════════════════
// NAV GROUP — voce principale + figli collapsible
//
// Tutta la riga e' un unico link navigabile.
// Il chevron e' DENTRO il link: click su tutta la riga = naviga.
// Click SOLO sul chevron (stopPropagation) = toggle expand.
// ════════════════════════════════════════════════════════════

function NavGroupItem({
  group,
  pathname,
  onNavigate,
}: {
  group: NavGroup;
  pathname: string;
  onNavigate?: () => void;
}) {
  const mainActive = isLinkActive(group.main, pathname);
  const childActive = group.children.some((c) => isLinkActive(c, pathname));
  const anyActive = mainActive || childActive;

  const [expanded, setExpanded] = useState(anyActive);
  const prevChildActive = useRef(childActive);

  useEffect(() => {
    if (childActive && !prevChildActive.current) setExpanded(true);
    prevChildActive.current = childActive;
  }, [childActive]);

  const toggleExpand = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setExpanded((prev) => !prev);
  }, []);

  return (
    <div>
      <Link
        href={group.main.href}
        onClick={() => { clearPageState(group.main.href); onNavigate?.(); }}
        data-guide={group.main.guideId}
        className={cn(
          "relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-150",
          mainActive
            ? "bg-primary/10 text-primary font-semibold before:absolute before:inset-y-[6px] before:left-0 before:w-[3px] before:rounded-full before:bg-primary before:content-['']"
            : childActive
              ? "text-primary/80 font-medium"
              : "text-foreground/90 hover:bg-accent/70 hover:text-foreground"
        )}
      >
        <group.main.icon className="h-4.5 w-4.5 shrink-0" />
        {group.main.label}

        {/* Chevron — click toggles expand, stopPropagation previene navigazione */}
        <span
          role="button"
          tabIndex={-1}
          onClick={toggleExpand}
          className="ml-auto flex h-5 w-5 items-center justify-center rounded transition-colors hover:bg-black/5 dark:hover:bg-white/10"
          aria-label={expanded ? `Chiudi ${group.main.label}` : `Espandi ${group.main.label}`}
        >
          <ChevronRight
            className={cn(
              "h-3 w-3 text-muted-foreground/50 transition-transform duration-200",
              expanded && "rotate-90",
            )}
          />
        </span>
      </Link>

      {/* Children */}
      <div
        className={cn(
          "overflow-hidden transition-all duration-200 ease-out",
          expanded ? "max-h-40 opacity-100" : "max-h-0 opacity-0"
        )}
      >
        <div className="space-y-0.5 py-0.5">
          {group.children.map((child) => (
            <NavItem key={child.href} item={child} pathname={pathname} onNavigate={onNavigate} indent />
          ))}
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// NAV UTILITY — Guida / Impostazioni (trattamento secondario)
// ════════════════════════════════════════════════════════════

function NavUtilityItem({
  item,
  pathname,
  onNavigate,
  showPulse,
}: {
  item: NavLink;
  pathname: string;
  onNavigate?: () => void;
  showPulse?: boolean;
}) {
  const active = isLinkActive(item, pathname);

  return (
    <Link
      href={item.href}
      onClick={() => { clearPageState(item.href); onNavigate?.(); }}
      data-guide={item.guideId}
      className={cn(
        "relative flex items-center gap-2.5 rounded-md px-3 py-1.5 text-[13px] transition-colors duration-150",
        active
          ? "text-primary font-medium"
          : "text-muted-foreground/70 hover:text-muted-foreground"
      )}
    >
      <item.icon className="h-3.5 w-3.5 shrink-0" />
      {item.label}
      {showPulse && (
        <span className="ml-auto">
          <span className="absolute inline-flex h-1.5 w-1.5 animate-ping rounded-full bg-primary opacity-75" />
          <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-primary" />
        </span>
      )}
    </Link>
  );
}

// ════════════════════════════════════════════════════════════
// SIDEBAR
// ════════════════════════════════════════════════════════════

interface SidebarProps {
  onNavigate?: () => void;
  guidePulse?: boolean;
}

export function Sidebar({ onNavigate, guidePulse }: SidebarProps) {
  const pathname = usePathname();
  const trainer = getStoredTrainer();
  const { theme, setTheme } = useTheme();

  return (
    <div className="flex h-full flex-col">
      {/* ── Logo ── */}
      <div className="flex h-16 items-center gap-3 px-5">
        <div className="flex h-[42px] w-[42px] shrink-0 items-center justify-center rounded-lg bg-primary shadow-[0_0_0_3px_oklch(0.52_0.14_173/0.15),0_2px_8px_oklch(0.52_0.14_173/0.25)]">
          <LogoIcon className="h-[23px] w-[23px] text-primary-foreground" />
        </div>
        <div className="min-w-0">
          <h1 className="text-[16px] font-bold leading-tight tracking-tight text-foreground">
            FitManager <span className="text-primary">Studio+</span>
          </h1>
          <p className="text-[10px] font-medium text-muted-foreground/60">{trainer ? `${trainer.nome} ${trainer.cognome}` : ""}</p>
        </div>
      </div>

      <Separator />

      {/* ── Search ── */}
      <div className="px-3 pt-3">
        <Button
          data-guide="sidebar-search"
          variant="outline"
          className="w-full justify-start gap-2 text-sm text-muted-foreground"
          onClick={() => window.dispatchEvent(new Event("open-command-palette"))}
        >
          <Search className="h-4 w-4" />
          <span className="flex-1 text-left">Cerca...</span>
          <kbd className="pointer-events-none rounded border bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
            Ctrl K
          </kbd>
        </Button>
      </div>

      {/* ── Main Nav ── */}
      <nav data-guide="sidebar-nav" className="flex flex-1 flex-col overflow-y-auto px-3 py-4">
        <div className="space-y-0.5">
          {NAV_TOP.map((entry) =>
            isGroup(entry) ? (
              <NavGroupItem key={entry.main.href} group={entry} pathname={pathname} onNavigate={onNavigate} />
            ) : (
              <NavItem key={entry.href} item={entry} pathname={pathname} onNavigate={onNavigate} />
            )
          )}
        </div>

        {/* ── Utility Nav (visivamente secondario) ── */}
        <div className="mt-auto space-y-0.5 pt-6">
          <Separator className="mb-3 opacity-50" />
          {NAV_BOTTOM.map((item) => (
            <NavUtilityItem
              key={item.href}
              item={item}
              pathname={pathname}
              onNavigate={onNavigate}
              showPulse={guidePulse && item.href === "/guida"}
            />
          ))}
        </div>
      </nav>

      {/* ── Trainer + Logout ── */}
      <div className="border-t p-4">
        {trainer && (
          <div className="mb-3 flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary ring-1 ring-primary/20">
              {trainer.nome[0]}
              {trainer.cognome[0]}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">
                {trainer.nome} {trainer.cognome}
              </p>
              <p className="text-xs text-muted-foreground">Trainer</p>
            </div>
          </div>
        )}
        <div className="flex gap-1">
          <Button
            variant="ghost"
            size="sm"
            className="flex-1 justify-start gap-2 text-muted-foreground hover:text-destructive"
            onClick={() => logout()}
          >
            <LogOut aria-hidden="true" className="h-4 w-4" />
            Esci
          </Button>
          <Button
            variant="ghost"
            size="icon-sm"
            className="shrink-0 text-muted-foreground hover:text-foreground"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            aria-label={theme === "dark" ? "Tema chiaro" : "Tema scuro"}
          >
            <Sun aria-hidden="true" className="h-4 w-4 rotate-0 scale-100 transition-transform dark:-rotate-90 dark:scale-0" />
            <Moon aria-hidden="true" className="absolute h-4 w-4 rotate-90 scale-0 transition-transform dark:rotate-0 dark:scale-100" />
          </Button>
        </div>
      </div>
    </div>
  );
}
