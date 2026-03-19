// src/components/nutrition/FoodSearchSidebar.tsx
"use client";

/**
 * Dialog full-width per ricerca e aggiunta alimenti a un pasto.
 *
 * Layout split: lista risultati a sinistra, dettaglio + grammi a destra.
 * Tab categorie raggruppate per logica (non 21 chip flat).
 * Batch mode: dopo ogni aggiunta torna alla lista (non chiude).
 *
 * v2: migrato da Sheet 400px a Dialog max-w-4xl per usabilità con 957 alimenti.
 */

import { useState, useEffect, useRef, useMemo } from "react";
import { Search, Loader2, Plus, ArrowLeft, Utensils, Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import { useFoods, useAddComponent, useDeleteComponent, useFoodDetail, useNutritionCategories } from "@/hooks/useNutrition";
import type { Food, FoodCategory } from "@/types/api";

// ── Raggruppamento categorie per tab ─────────────────────────────────────
// 21 categorie DB → 7 tab logici per il trainer

interface CategoryTab {
  label: string;
  categoryIds: number[];
}

const CATEGORY_TABS: CategoryTab[] = [
  { label: "Tutti", categoryIds: [] },
  { label: "Verdure e frutta", categoryIds: [5, 6, 7] },
  { label: "Carne e pesce", categoryIds: [8, 9, 10, 11] },
  { label: "Latticini e uova", categoryIds: [12] },
  { label: "Cereali e pane", categoryIds: [1, 2, 3, 4] },
  { label: "Piatti pronti", categoryIds: [16, 17, 18, 19, 20, 21] },
  { label: "Altro", categoryIds: [13, 14, 15] },
];

// ── Props (identiche al vecchio FoodSearchSidebar) ───────────────────────

interface FoodSearchSidebarProps {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  planId: number;
  mealId: number | null;
  mealLabel?: string;
  replaceCompId?: number | null;
}

// ── Componente ───────────────────────────────────────────────────────────

export function FoodSearchSidebar({
  open,
  onOpenChange,
  planId,
  mealId,
  mealLabel,
  replaceCompId,
}: FoodSearchSidebarProps) {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [selectedFood, setSelectedFood] = useState<Food | null>(null);
  const [quantita, setQuantita] = useState<string>("100");
  const [addedCount, setAddedCount] = useState(0);
  const [activeTabIdx, setActiveTabIdx] = useState(0);
  const searchRef = useRef<HTMLInputElement>(null);

  const addComponent = useAddComponent();
  const deleteComponent = useDeleteComponent();
  const { data: categories = [] } = useNutritionCategories();

  // Risolvi category IDs dal tab attivo
  const activeCategoryIds = CATEGORY_TABS[activeTabIdx]?.categoryIds ?? [];
  // Se tab "Tutti" (ids vuoto) → nessun filtro categoria
  const categoryIdParam = activeCategoryIds.length === 1 ? activeCategoryIds[0] : undefined;

  const { data: rawFoods = [], isLoading } = useFoods(
    debouncedQuery || undefined,
    categoryIdParam,
  );

  // Filtro client-side per tab con categorie multiple (es. "Verdure e frutta" = 3 cat)
  const foods = useMemo(() => {
    if (activeCategoryIds.length <= 1) return rawFoods;
    const catSet = new Set(activeCategoryIds);
    return rawFoods.filter((f) => catSet.has(f.categoria_id));
  }, [rawFoods, activeCategoryIds]);

  const { data: foodDetail } = useFoodDetail(selectedFood?.id ?? null);
  const hasQuery = debouncedQuery.length >= 2 || activeCategoryIds.length > 0;

  // Debounce
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 400);
    return () => clearTimeout(timer);
  }, [query]);

  // Reset on meal change
  useEffect(() => {
    setQuery("");
    setDebouncedQuery("");
    setSelectedFood(null);
    setQuantita("100");
    setAddedCount(0);
    setActiveTabIdx(0);
  }, [mealId]);

  // Autofocus
  useEffect(() => {
    if (open && !selectedFood) {
      setTimeout(() => searchRef.current?.focus(), 150);
    }
  }, [open, selectedFood]);

  const handleSelect = (food: Food) => {
    setSelectedFood(food);
    setQuantita("100");
  };

  const handleBack = () => {
    setSelectedFood(null);
    setQuantita("100");
    setTimeout(() => searchRef.current?.focus(), 100);
  };

  const handleAdd = async () => {
    if (!selectedFood || mealId === null) return;
    const g = parseFloat(quantita);
    if (!g || g <= 0) return;

    if (replaceCompId != null) {
      await deleteComponent.mutateAsync({ planId, mealId, compId: replaceCompId });
    }

    await addComponent.mutateAsync({
      planId,
      mealId,
      alimento_id: selectedFood.id,
      quantita_g: g,
    });

    if (replaceCompId != null) {
      toast.success(`${selectedFood.nome} sostituito`);
      onOpenChange(false);
      return;
    }

    toast.success(`${selectedFood.nome} aggiunto`);
    setAddedCount((n) => n + 1);
    setSelectedFood(null);
    setQuantita("100");
    setQuery("");
    setDebouncedQuery("");
    setTimeout(() => searchRef.current?.focus(), 100);
  };

  // Macro scalate
  const qty = parseFloat(quantita || "0");
  const scaledMacro = selectedFood && qty > 0
    ? {
        kcal: Math.round((selectedFood.energia_kcal * qty) / 100),
        p: Math.round((selectedFood.proteine_g * qty) / 100 * 10) / 10,
        c: Math.round((selectedFood.carboidrati_g * qty) / 100 * 10) / 10,
        g: Math.round((selectedFood.grassi_g * qty) / 100 * 10) / 10,
      }
    : null;

  const headerTitle = replaceCompId != null
    ? "Sostituisci alimento"
    : mealLabel
    ? `Aggiungi a ${mealLabel}`
    : "Aggiungi alimento";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl h-[85vh] flex flex-col gap-0 p-0 overflow-hidden">
        {/* Header compatto */}
        <div className="flex items-center justify-between px-6 py-4 border-b shrink-0">
          <DialogHeader className="p-0 space-y-0">
            <DialogTitle className="flex items-center gap-2.5 text-base font-semibold">
              <Utensils className="h-4.5 w-4.5 text-teal-600 shrink-0" />
              {headerTitle}
            </DialogTitle>
          </DialogHeader>
          {addedCount > 0 && (
            <span className="flex items-center gap-1.5 rounded-full bg-emerald-50 border border-emerald-200 px-3 py-1 text-xs font-semibold text-emerald-700">
              <Check className="h-3 w-3" />
              {addedCount} {addedCount === 1 ? "aggiunto" : "aggiunti"}
            </span>
          )}
        </div>

        {/* Search bar + tabs — riga unica */}
        <div className="flex items-center gap-4 px-6 py-3 border-b bg-muted/10 shrink-0">
          <div className="relative w-72 shrink-0">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              ref={searchRef}
              placeholder="Cerca alimento..."
              className="pl-9 h-9 text-sm bg-background"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-0.5 min-w-0">
            {CATEGORY_TABS.map((tab, idx) => (
              <button
                key={tab.label}
                onClick={() => setActiveTabIdx(idx)}
                className={`whitespace-nowrap px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  activeTabIdx === idx
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Body: split 60/40 */}
        <div className="flex-1 flex min-h-0">
          {/* LEFT: lista risultati (60%) */}
          <ScrollArea className="w-[60%] shrink-0 border-r">
            {isLoading && (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            )}
            {!isLoading && !hasQuery && (
              <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
                <Search className="h-7 w-7 mb-2 opacity-20" />
                <p className="text-sm">Cerca per nome o seleziona una categoria</p>
              </div>
            )}
            {!isLoading && hasQuery && foods.length === 0 && (
              <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
                <p className="text-sm">Nessun alimento trovato</p>
              </div>
            )}
            {foods.map((food) => (
              <button
                key={food.id}
                onClick={() => handleSelect(food)}
                className={`w-full flex items-baseline justify-between gap-3 px-5 py-2.5 text-left transition-colors border-b border-border/40 hover:bg-accent/50 ${
                  selectedFood?.id === food.id ? "bg-accent" : ""
                }`}
              >
                <div className="min-w-0">
                  <div className="font-medium text-sm truncate">{food.nome}</div>
                  {food.categoria_nome && (
                    <div className="text-[11px] text-muted-foreground/50 mt-0.5">{food.categoria_nome}</div>
                  )}
                </div>
                <div className="flex items-center gap-2.5 text-xs tabular-nums shrink-0">
                  <span className="font-semibold w-12 text-right">{Math.round(food.energia_kcal)}</span>
                  <span className="text-blue-600 w-8 text-right">P{food.proteine_g}</span>
                  <span className="text-amber-600 w-8 text-right">C{food.carboidrati_g}</span>
                  <span className="text-rose-500 w-8 text-right">G{food.grassi_g}</span>
                </div>
              </button>
            ))}
          </ScrollArea>

          {/* RIGHT: dettaglio + grammi (40%) */}
          <div className="w-[40%] shrink-0 flex flex-col bg-muted/5">
            {!selectedFood ? (
              <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground/40 px-8">
                <Utensils className="h-10 w-10 mb-3" />
                <p className="text-sm text-center text-muted-foreground/60">
                  Seleziona un alimento dalla lista
                </p>
              </div>
            ) : (
              <div className="flex-1 flex flex-col overflow-y-auto">
                {/* Card alimento */}
                <div className="px-6 pt-6 pb-4">
                  <h3 className="text-lg font-bold leading-snug">{selectedFood.nome}</h3>
                  {selectedFood.categoria_nome && (
                    <p className="text-xs text-muted-foreground mt-1">{selectedFood.categoria_nome}</p>
                  )}
                  <div className="mt-3 grid grid-cols-4 gap-1 text-center rounded-lg bg-muted/30 py-2.5 px-2">
                    <div>
                      <div className="text-sm font-bold tabular-nums">{Math.round(selectedFood.energia_kcal)}</div>
                      <div className="text-[10px] text-muted-foreground">kcal</div>
                    </div>
                    <div>
                      <div className="text-sm font-bold tabular-nums text-blue-600">{selectedFood.proteine_g}g</div>
                      <div className="text-[10px] text-muted-foreground">Prot</div>
                    </div>
                    <div>
                      <div className="text-sm font-bold tabular-nums text-amber-600">{selectedFood.carboidrati_g}g</div>
                      <div className="text-[10px] text-muted-foreground">Carb</div>
                    </div>
                    <div>
                      <div className="text-sm font-bold tabular-nums text-rose-500">{selectedFood.grassi_g}g</div>
                      <div className="text-[10px] text-muted-foreground">Grassi</div>
                    </div>
                  </div>
                  <p className="text-[10px] text-muted-foreground/50 text-right mt-1">per 100g</p>
                </div>

                <Separator />

                {/* Quantità */}
                <div className="px-6 py-4 space-y-3">
                  <label className="text-sm font-semibold">Quantità (grammi)</label>
                  <Input
                    type="number"
                    min={1}
                    max={2000}
                    autoFocus
                    value={quantita}
                    onChange={(e) => setQuantita(e.target.value)}
                    className="text-right tabular-nums h-10 text-base font-semibold"
                  />
                  <div className="flex flex-wrap gap-1.5">
                    {(foodDetail?.porzioni?.length
                      ? foodDetail.porzioni.slice(0, 8).map((p) => ({
                          key: String(p.id),
                          label: `${p.nome} (${p.grammi}g)`,
                          grams: p.grammi,
                        }))
                      : [30, 50, 80, 100, 150, 200].map((g_val) => ({
                          key: String(g_val),
                          label: `${g_val}g`,
                          grams: g_val,
                        }))
                    ).map((item) => (
                      <button
                        key={item.key}
                        type="button"
                        onClick={() => setQuantita(String(item.grams))}
                        className={`rounded-md border px-2.5 py-1 text-xs font-medium transition-colors ${
                          quantita === String(item.grams)
                            ? "border-primary bg-primary text-primary-foreground"
                            : "border-border text-muted-foreground hover:border-primary/60 hover:text-foreground hover:bg-muted/50"
                        }`}
                      >
                        {item.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Macro scalate — risultato */}
                {scaledMacro && (
                  <div className="px-6 pb-4">
                    <div className="rounded-xl border bg-gradient-to-br from-teal-50/80 to-emerald-50/40 dark:from-teal-950/30 dark:to-emerald-950/20 p-4">
                      <p className="text-[11px] font-semibold text-muted-foreground mb-2 uppercase tracking-wider">
                        Per {quantita}g
                      </p>
                      <div className="grid grid-cols-4 gap-1 text-center">
                        <div>
                          <div className="text-xl font-bold tabular-nums">{scaledMacro.kcal}</div>
                          <div className="text-[10px] text-muted-foreground">kcal</div>
                        </div>
                        <div>
                          <div className="text-xl font-bold tabular-nums text-blue-600">{scaledMacro.p}g</div>
                          <div className="text-[10px] text-muted-foreground">Prot</div>
                        </div>
                        <div>
                          <div className="text-xl font-bold tabular-nums text-amber-600">{scaledMacro.c}g</div>
                          <div className="text-[10px] text-muted-foreground">Carb</div>
                        </div>
                        <div>
                          <div className="text-xl font-bold tabular-nums text-rose-500">{scaledMacro.g}g</div>
                          <div className="text-[10px] text-muted-foreground">Grassi</div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* CTA fisso in fondo */}
                <div className="mt-auto px-6 py-4 border-t bg-background">
                  <Button
                    className="w-full h-10"
                    onClick={handleAdd}
                    disabled={
                      addComponent.isPending ||
                      deleteComponent.isPending ||
                      !quantita ||
                      parseFloat(quantita) <= 0 ||
                      mealId === null
                    }
                  >
                    {addComponent.isPending || deleteComponent.isPending ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Plus className="mr-2 h-4 w-4" />
                    )}
                    {replaceCompId != null ? "Sostituisci" : "Aggiungi al pasto"}
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
