// src/components/contracts/ReopenContractDialog.tsx
"use client";

/**
 * Riapertura di un contratto chiuso (G7.4) — dialog di conferma con riepilogo di cosa viene invertito.
 *
 * `reopen` è l'inverso esplicito di terminate/auto-close: annulla l'eventuale rimborso (rimuove il
 * movimento di cassa USCITA), ripristina il residuo (storno→0) e le rate non saldate, riporta il
 * contratto ad aperto. Conferma esplicita perché tocca il libro mastro (annulla un rimborso registrato).
 */

import { Loader2, RotateCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useReopenContract } from "@/hooks/useContracts";
import { formatCurrency } from "@/lib/format";
import type { ContractListItem } from "@/types/api";

interface ReopenContractDialogProps {
  contract: ContractListItem | null;
  clientLabel: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ReopenContractDialog({
  contract,
  clientLabel,
  open,
  onOpenChange,
}: ReopenContractDialogProps) {
  const reopen = useReopenContract();
  const hadRefund = (contract?.totale_rimborsato ?? 0) > 0.009;

  const handleReopen = () => {
    if (contract === null) return;
    reopen.mutate(contract.id, { onSuccess: () => onOpenChange(false) });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <RotateCcw className="h-4.5 w-4.5 text-sky-600 dark:text-sky-400" />
            Riapri contratto — {clientLabel}
          </DialogTitle>
          <DialogDescription>
            Annulla la chiusura e riporta il contratto ad aperto. È l&apos;inverso della terminazione.
          </DialogDescription>
        </DialogHeader>

        <ul className="space-y-1.5 text-sm text-muted-foreground">
          {hadRefund ? (
            <li className="text-amber-700 dark:text-amber-300">
              • Il rimborso di {formatCurrency(contract!.totale_rimborsato)} registrato verrà{" "}
              <span className="font-medium">annullato</span> (il movimento di cassa in uscita sarà rimosso).
            </li>
          ) : null}
          <li>• Il residuo del contratto tornerà dovuto (lo storno viene azzerato).</li>
          <li>• Le rate non saldate eliminate alla terminazione vengono ripristinate.</li>
        </ul>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={reopen.isPending}>
            Annulla
          </Button>
          <Button onClick={handleReopen} disabled={contract === null || reopen.isPending}>
            {reopen.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            Riapri contratto
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
