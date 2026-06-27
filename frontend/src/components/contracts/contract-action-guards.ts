import type { ContractLifecycle } from "@/types/api";

interface ContractResiduoLike {
  chiuso: boolean;
  lifecycle: ContractLifecycle;
  residuo: number;
}

// G6/G7: il residuo e' incassabile direttamente solo sui contratti scaduti ma ancora aperti.
export function getIncassaResiduoAmount(contract: ContractResiduoLike): number {
  if (contract.chiuso) return 0;
  if (contract.lifecycle !== "sospeso" && contract.lifecycle !== "esaurito") return 0;
  return contract.residuo;
}