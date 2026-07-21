// src/app/(dashboard)/clienti/[id]/page.tsx
"use client";

/**
 * Profilo Cliente — Hub Operativo.
 *
 * Layout:
 * - ProfileHeader (persistente): avatar, nome, contatti, stato, modifica
 * - OnboardingChecklist: hero CTA + stepper 5 step (solo se profilo incompleto)
 * - ProfileKpi: 4 card KPI
 * - Tabs: Panoramica (Journey Hub) | Contratti | Sessioni | Movimenti | Schede
 *   con dot di completamento sui tab label
 */

import { use, useState, useCallback, useMemo, useRef, useEffect } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import {
  FileText, Calendar, Wallet, User,
  ClipboardList, TrendingUp,
} from "lucide-react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { AvatarHero } from "@/components/clients/AvatarHero";
import { ClientSheet } from "@/components/clients/ClientSheet";
import { ContractSheet } from "@/components/contracts/ContractSheet";
import { TemplateSelector } from "@/components/workouts/TemplateSelector";
import { OnboardingChecklist } from "@/components/clients/profile/OnboardingChecklist";
import { PanoramicaTab } from "@/components/clients/profile/PanoramicaTab";
import { ContrattiTab } from "@/components/clients/profile/ContrattiTab";
import { SessioniTab } from "@/components/clients/profile/SessioniTab";
import { MovimentiTab } from "@/components/clients/profile/MovimentiTab";
import { SchedeTab } from "@/components/clients/profile/SchedeTab";
import { AllenamentoTab } from "@/components/clients/profile/AllenamentoTab";
import { DataErrorState, ProfileSkeleton, NotFoundState } from "@/components/clients/profile/ProfileShared";

import { useClient } from "@/hooks/useClients";
import { useClientContracts } from "@/hooks/useContracts";
import { useClientEvents } from "@/hooks/useAgenda";
import { useClientReadiness, computeOnboardingSteps } from "@/hooks/useClientReadiness";
import { useClientAvatar } from "@/hooks/useWorkspace";
import { isNotFoundError } from "@/lib/query-error";
import { resolveBackNavigation } from "@/lib/url-state";

// ════════════════════════════════════════════════════════════
// PAGE
// ════════════════════════════════════════════════════════════

export default function ClientProfilePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const clientId = parseInt(id, 10);
  const validClientId = Number.isInteger(clientId) && clientId > 0 ? clientId : null;

  const clientQuery = useClient(validClientId);
  const avatarQuery = useClientAvatar(clientId, validClientId !== null);
  const readinessQuery = useClientReadiness(validClientId ?? 0);
  const contractsQuery = useClientContracts(validClientId);
  const eventsQuery = useClientEvents(validClientId);
  const { data: client, isLoading } = clientQuery;
  const { data: avatar, isLoading: avatarLoading } = avatarQuery;
  const { readiness } = readinessQuery;
  const contractsData = contractsQuery.data;
  const eventsData = eventsQuery.data;
  const [sheetOpen, setSheetOpen] = useState(false);
  const [contractSheetOpen, setContractSheetOpen] = useState(false);
  const [templateSelectorOpen, setTemplateSelectorOpen] = useState(false);
  const autoOpenSchedaConsumedRef = useRef(false);

  // ── URL-backed tab state ──
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();
  const activeTab = searchParams.get("tab") ?? "panoramica";
  const shouldAutoOpenScheda = searchParams.get("startScheda") === "1";
  const rawReturnTo = searchParams.get("returnTo");
  const fromParam = searchParams.get("from");
  const returnTo = rawReturnTo && rawReturnTo.startsWith("/") && !rawReturnTo.startsWith("//") ? rawReturnTo : null;
  const backNav = resolveBackNavigation(fromParam, { href: "/clienti", label: "Torna ai clienti" });
  const backHref = returnTo ?? backNav.href;
  const backLabel = returnTo?.startsWith("/rinnovi-incassi")
    ? "Torna a Rinnovi & Incassi"
    : backNav.label;
  const partialSources = [
    contractsQuery.isError ? "contratti" : null,
    eventsQuery.isError ? "sessioni" : null,
    readinessQuery.isError ? "riepilogo clinico" : null,
  ].filter((source): source is string => source !== null);
  const hasPartialData = partialSources.length > 0;
  const isPartialRetrying = contractsQuery.isFetching || eventsQuery.isFetching || readinessQuery.isFetching;

  const retryProfile = () => {
    void clientQuery.refetch();
  };

  const retryPartialData = () => {
    void Promise.all([
      contractsQuery.refetch(),
      eventsQuery.refetch(),
      readinessQuery.refetch(),
    ]);
  };

  const handleTabChange = useCallback((value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value === "panoramica") params.delete("tab");
    else params.set("tab", value);
    const qs = params.toString();
    router.replace(`${pathname}${qs ? `?${qs}` : ""}`, { scroll: false });
  }, [searchParams, pathname, router]);

  // Auto-open scheda template selector
  useEffect(() => {
    if (!shouldAutoOpenScheda || autoOpenSchedaConsumedRef.current) return;
    autoOpenSchedaConsumedRef.current = true;
    const params = new URLSearchParams(searchParams.toString());
    params.delete("startScheda");
    const qs = params.toString();
    router.replace(`${pathname}${qs ? `?${qs}` : ""}`, { scroll: false });
    const rafId = requestAnimationFrame(() => setTemplateSelectorOpen(true));
    return () => cancelAnimationFrame(rafId);
  }, [shouldAutoOpenScheda, searchParams, router, pathname]);

  // Onboarding steps from real data — contratto opens sheet inline
  const onboardingSteps = useMemo(() => {
    const contracts = contractsData?.items ?? [];
    const activeContracts = contracts.filter((c) => !c.chiuso);
    const orphan = activeContracts.find((c) => c.rate_totali === 0 && (c.prezzo_totale ?? 0) > 0);
    const steps = computeOnboardingSteps(clientId, readiness, {
      hasContracts: contracts.length > 0,
      hasContractWithRates: activeContracts.some((c) => c.rate_totali > 0),
      orphanContractId: orphan?.id ?? null,
      hasEvents: (eventsData?.items?.length ?? 0) > 0,
    });
    // Contratto step senza contratti: apre la ContractSheet precompilata
    // Contratto step con contratto orfano: naviga al dettaglio (href gia' impostato)
    const contrattoStep = steps.find((s) => s.key === "contratto");
    if (contrattoStep && !contrattoStep.completed && !orphan) {
      contrattoStep.onAction = () => setContractSheetOpen(true);
    }
    return steps;
  }, [clientId, readiness, contractsData, eventsData]);

  // Tab completion dots
  const tabComplete = useMemo(() => ({
    contratti: (contractsData?.items?.length ?? 0) > 0,
    sessioni: (eventsData?.items?.length ?? 0) > 0,
    schede: readiness?.has_workout_plan ?? false,
  }), [contractsData, eventsData, readiness]);

  if (validClientId === null) return <NotFoundState />;
  if (isLoading) return <ProfileSkeleton />;
  if (clientQuery.isError) {
    if (isNotFoundError(clientQuery.error)) return <NotFoundState />;
    return (
      <DataErrorState
        title="Impossibile aprire il profilo cliente"
        message="Il cliente non è stato verificato. Controlla la connessione e riprova."
        onRetry={retryProfile}
        isRetrying={clientQuery.isFetching}
      />
    );
  }
  if (!client) {
    return (
      <DataErrorState
        title="Profilo cliente non disponibile"
        message="La richiesta è terminata senza dati verificabili. Riprova il caricamento."
        onRetry={retryProfile}
        isRetrying={clientQuery.isFetching}
      />
    );
  }

  return (
    <div className="space-y-4">
      <div data-guide="client-avatar-hero">
        <AvatarHero
          client={client}
          avatar={avatar ?? null}
          isLoading={avatarLoading}
          onEdit={() => setSheetOpen(true)}
          onTabChange={handleTabChange}
          backHref={backHref}
          backLabel={backLabel}
        />
      </div>

      {hasPartialData ? (
        <DataErrorState
          title="Profilo disponibile con dati parziali"
          message={`Non è stato possibile verificare: ${partialSources.join(", ")}. Gli indicatori dipendenti restano nascosti.`}
          onRetry={retryPartialData}
          isRetrying={isPartialRetrying}
        />
      ) : null}

      {/* Onboarding Checklist — hero CTA + stepper (solo se profilo incompleto) */}
      {!hasPartialData ? (
        <div data-guide="client-onboarding-checklist">
          <OnboardingChecklist steps={onboardingSteps} />
        </div>
      ) : null}

      {/* Tabs con completion dots — sticky per visibilita' permanente */}
      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList className="sticky top-0 z-20 w-full overflow-x-auto bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
          <TabsTrigger value="panoramica">
            <User className="mr-2 h-4 w-4" />
            Panoramica
          </TabsTrigger>
          <TabsTrigger value="contratti">
            <FileText className="mr-2 h-4 w-4" />
            Contratti
            {!contractsQuery.isError && tabComplete.contratti ? <CompletionDot /> : null}
          </TabsTrigger>
          <TabsTrigger value="sessioni">
            <Calendar className="mr-2 h-4 w-4" />
            Sessioni
            {!eventsQuery.isError && tabComplete.sessioni ? <CompletionDot /> : null}
          </TabsTrigger>
          <TabsTrigger value="movimenti">
            <Wallet className="mr-2 h-4 w-4" />
            Movimenti
          </TabsTrigger>
          <TabsTrigger value="schede">
            <ClipboardList className="mr-2 h-4 w-4" />
            Schede
            {!readinessQuery.isError && tabComplete.schede ? <CompletionDot /> : null}
          </TabsTrigger>
          <TabsTrigger value="allenamento">
            <TrendingUp className="mr-2 h-4 w-4" />
            Allenamento
          </TabsTrigger>
        </TabsList>

        <TabsContent value="panoramica" className="mt-4">
          {hasPartialData ? (
            <DataErrorState
              title="Panoramica operativa non verificata"
              message="Riprova i dati del profilo prima di usare il percorso consigliato."
              onRetry={retryPartialData}
              isRetrying={isPartialRetrying}
            />
          ) : (
            <PanoramicaTab
              client={client}
              clientId={clientId}
              readiness={readiness}
              hasContracts={(contractsData?.items?.length ?? 0) > 0}
              hasContractWithRates={(contractsData?.items ?? []).some((c) => !c.chiuso && c.rate_totali > 0)}
              hasEvents={(eventsData?.items?.length ?? 0) > 0}
              onTabChange={handleTabChange}
            />
          )}
        </TabsContent>
        <TabsContent value="contratti" className="mt-4">
          <ContrattiTab clientId={clientId} />
        </TabsContent>
        <TabsContent value="sessioni" className="mt-4">
          <SessioniTab clientId={clientId} />
        </TabsContent>
        <TabsContent value="movimenti" className="mt-4">
          <MovimentiTab clientId={clientId} />
        </TabsContent>
        <TabsContent value="schede" className="mt-4">
          <SchedeTab clientId={clientId} onNewScheda={() => setTemplateSelectorOpen(true)} fromContext={searchParams.get("from") ?? undefined} />
        </TabsContent>
        <TabsContent value="allenamento" className="mt-4">
          <AllenamentoTab clientId={clientId} />
        </TabsContent>
      </Tabs>

      <TemplateSelector
        open={templateSelectorOpen}
        onOpenChange={setTemplateSelectorOpen}
        clientId={clientId}
        fromContext={searchParams.get("from") ?? undefined}
      />
      <ClientSheet
        open={sheetOpen}
        onOpenChange={setSheetOpen}
        client={client}
      />
      <ContractSheet
        open={contractSheetOpen}
        onOpenChange={setContractSheetOpen}
        defaultClientId={clientId}
      />
    </div>
  );
}

/** Dot verde accanto al label tab — indica che il tab ha contenuto. */
function CompletionDot() {
  return (
    <span className="ml-1.5 inline-block h-1.5 w-1.5 rounded-full bg-emerald-500" />
  );
}
