// src/components/contracts/ContractSheet.tsx
"use client";

/**
 * Sheet laterale per creare/modificare un contratto.
 *
 * Pattern da ClientSheet: apre da destra, contiene il form,
 * si chiude su successo della mutation (con conferma se dirty).
 */

import { useCallback, useRef } from "react";
import { useRouter } from "next/navigation";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { ContractForm, type ContractSubmitPayload, type RenewalDefaults } from "./ContractForm";
import { useCreateContract, useUpdateContract, useRenewContract } from "@/hooks/useContracts";
import type { Contract } from "@/types/api";
import { toISOLocal } from "@/lib/format";

interface ContractSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  contract?: Contract | null;
  defaultClientId?: number;
  /** When set, form is pre-filled and useRenewContract is used instead of useCreateContract. */
  renewContractId?: number;
  renewalDefaults?: RenewalDefaults;
}

export function ContractSheet({
  open,
  onOpenChange,
  contract,
  defaultClientId,
  renewContractId,
  renewalDefaults,
}: ContractSheetProps) {
  const router = useRouter();
  const isEdit = !!contract;
  const isRenewal = !!renewContractId;
  const createMutation = useCreateContract();
  const updateMutation = useUpdateContract();
  const renewMutation = useRenewContract();

  const isPending = createMutation.isPending || updateMutation.isPending || renewMutation.isPending;

  // Protezione chiusura accidentale
  const dirtyRef = useRef(false);
  const handleDirtyChange = useCallback((d: boolean) => { dirtyRef.current = d; }, []);
  const guardedOpenChange = useCallback((newOpen: boolean) => {
    if (!newOpen && dirtyRef.current) {
      if (!window.confirm("Hai modifiche non salvate. Vuoi davvero uscire?")) return;
    }
    dirtyRef.current = false;
    onOpenChange(newOpen);
  }, [onOpenChange]);

  const requiresBackdateConfirm = useCallback((values: ContractSubmitPayload) => {
    if (!contract || contract.lifecycle !== "attivo") return false;
    if (!values.data_scadenza) return false;
    const todayLocal = toISOLocal(new Date()).slice(0, 10);
    return values.data_scadenza < todayLocal;
  }, [contract]);

  const handleSubmit = (values: ContractSubmitPayload) => {
    const onSuccess = () => { dirtyRef.current = false; onOpenChange(false); };
    if (isEdit) {
      if (requiresBackdateConfirm(values)) {
        const confirmed = window.confirm(
          "Stai impostando una scadenza nel passato. Il contratto risultera' immediatamente scaduto; lo stato reale verra' poi derivato in base ai crediti residui. Vuoi continuare?"
        );
        if (!confirmed) return;
      }
      const { id_cliente: _id_cliente, acconto: _acconto, metodo_acconto: _metodo_acconto, ...updatePayload } = values;
      updateMutation.mutate({ id: contract.id, ...updatePayload }, { onSuccess });
    } else if (isRenewal && renewContractId) {
      // Dopo il rinnovo, conduci il trainer direttamente al piano rate del nuovo
      // contratto (§A — passaggio guidato). La tab "Piano Pagamenti" e' il default
      // del dettaglio: con zero rate apre subito il form di generazione.
      renewMutation.mutate(
        { contractId: renewContractId, ...values },
        {
          onSuccess: (newContract) => {
            dirtyRef.current = false;
            onOpenChange(false);
            if (newContract?.id) router.push(`/contratti/${newContract.id}?from=rinnovi-incassi`);
          },
        },
      );
    } else {
      createMutation.mutate(values, { onSuccess });
    }
  };

  return (
    <Sheet open={open} onOpenChange={guardedOpenChange}>
      <SheetContent className="overflow-y-auto sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>
            {isEdit ? "Modifica Contratto" : isRenewal ? "Rinnova Contratto" : "Nuovo Contratto"}
          </SheetTitle>
        </SheetHeader>
        <div className="mt-6">
          <ContractForm
            key={contract?.id ?? renewContractId ?? "new"}
            contract={contract}
            defaultClientId={defaultClientId}
            renewalDefaults={renewalDefaults}
            onSubmit={handleSubmit}
            isPending={isPending}
            onDirtyChange={handleDirtyChange}
          />
        </div>
      </SheetContent>
    </Sheet>
  );
}
