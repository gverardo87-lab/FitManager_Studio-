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
      <DialogContent className="max-w-4xl h-[80vh] flex flex-col gap-0 p-0 overflow-hidden">
        {/* Header */}
        <DialogHeader className="px-6 pt-5 pb-4 border-b shrink-0">
          <div className="flex items-center gap-3">
            <DialogTitle className="flex-1 flex items-center gap-2 text-lg">
              <Utensils className="h-5 w-5 text-teal-600 shrink-0" />
              {headerTitle}
            </DialogTitle>
            {addedCount > 0 && (
              <span className="flex items-center gap-1 rounded-full bg-emerald-100 px-3 py-1 text-sm font-semibold text-emerald-700">
                <Check className="h-3.5 w-3.5" />
                {addedCount} {addedCount === 1 ? "aggiunto" : "aggiunti"}
              </span>
            )}
          </div>
        </DialogHeader>

        {/* Search + Tab bar */}
        <div className="px-6 pt-4 pb-3 space-y-3 shrink-0 border-b bg-muted/20">
          {/* Search input */}
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              ref={searchRef}
              placeholder="Cerca per nome (es. riso, pollo, yogurt...)"
              className="pl-9 h-11 text-base bg-background"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          {/* Category tabs */}
          <div className="flex gap-1 overflow-x-auto pb-0.5">
            {CATEGORY_TABS.map((tab, idx) => (
              <button
                key={tab.label}
                onClick={() => setActiveTabIdx(idx)}
                className={`whitespace-nowrap rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors ${
                  activeTabIdx === idx
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Body: split panel */}
        <div className="flex-1 flex min-h-0">
          {/* LEFT: risultati */}
          <div className="flex-1 min-w-0 border-r">
            <ScrollArea className="h-full">
              {isLoading && (
                <div className="flex items-center justify-center py-16">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                </div>
              )}
              {!isLoading && !hasQuery && (
                <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                  <Search className="h-8 w-8 mb-3 opacity-30" />
                  <p className="text-sm">Cerca per nome o seleziona una categoria</p>
                </div>
              )}
              {!isLoading && hasQuery && foods.length === 0 && (
                <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                  <p className="text-sm">Nessun alimento trovato</p>
                </div>
              )}
              <div className="divide-y">
                {foods.map((food) => (
                  <button
                    key={food.id}
                    onClick={() => handleSelect(food)}
                    className={`w-full px-5 py-3 text-left transition-colors hover:bg-accent ${
                      selectedFood?.id === food.id ? "bg-accent" : ""
                    }`}
                  >
                    <div className="font-semibold text-sm leading-tight">{food.nome}</div>
                    <div className="mt-1 flex items-center gap-2 text-xs">
                      {food.categoria_nome && (
                        <span className="text-muted-foreground/60 font-medium">
                          {food.categoria_nome}
                        </span>
                      )}
                      <span className="text-muted-foreground tabular-nums">
                        {Math.round(food.energia_kcal)} kcal
                      </span>
                      <span className="text-blue-600 tabular-nums">P{food.proteine_g}</span>
                      <span className="text-amber-600 tabular-nums">C{food.carboidrati_g}</span>
                      <span className="text-rose-500 tabular-nums">G{food.grassi_g}</span>
                    </div>
                  </button>
                ))}
              </div>
            </ScrollArea>
          </div>

          {/* RIGHT: dettaglio + grammi */}
          <div className="w-[340px] shrink-0 flex flex-col">
            {!selectedFood ? (
              <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground px-6">
                <ArrowLeft className="h-6 w-6 mb-3 opacity-30" />
                <p className="text-sm text-center">
                  Seleziona un alimento dalla lista
                </p>
              </div>
            ) : (
              <div className="flex-1 flex flex-col p-5 gap-5 overflow-y-auto">
                {/* Nome + macro base */}
                <div>
                  <h3 className="text-base font-bold leading-tight">{selectedFood.nome}</h3>
                  {selectedFood.categoria_nome && (
                    <p className="text-sm text-muted-foreground mt-0.5">{selectedFood.categoria_nome}</p>
                  )}
                  <div className="mt-2 flex items-center gap-2 text-sm">
                    <span className="tabular-nums font-medium">{Math.round(selectedFood.energia_kcal)} kcal</span>
                    <span className="text-muted-foreground/30">·</span>
                    <span className="text-blue-600 tabular-nums font-medium">P{selectedFood.proteine_g}g</span>
                    <span className="text-muted-foreground/30">·</span>
                    <span className="text-amber-600 tabular-nums font-medium">C{selectedFood.carboidrati_g}g</span>
                    <span className="text-muted-foreground/30">·</span>
                    <span className="text-rose-500 tabular-nums font-medium">G{selectedFood.grassi_g}g</span>
                    <span className="text-xs text-muted-foreground/40">/ 100g</span>
                  </div>
                </div>

                <Separator />

                {/* Quantità */}
                <div className="space-y-2">
                  <label className="text-sm font-semibold">Quantità (grammi)</label>
                  <Input
                    type="number"
                    min={1}
                    max={2000}
                    autoFocus
                    value={quantita}
                    onChange={(e) => setQuantita(e.target.value)}
                    className="text-right tabular-nums h-11 text-base font-semibold"
                  />
                  <div className="flex flex-wrap gap-1.5">
                    {(foodDetail?.porzioni?.length
                      ? foodDetail.porzioni.slice(0, 8).map((p) => ({
                          key: String(p.id),
                          label: `${p.nome} (${p.grammi}g)`,
                          grams: p.grammi,
                        }))
                      : [30, 50, 80, 100, 150, 200].map((g) => ({
                          key: String(g),
                          label: `${g}g`,
                          grams: g,
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

                {/* Macro scalate */}
                {scaledMacro && (
                  <div className="rounded-lg bg-muted/40 px-4 py-4">
                    <p className="text-xs font-semibold text-muted-foreground mb-2.5 uppercase tracking-wider">
                      Per {quantita}g
                    </p>
                    <div className="grid grid-cols-4 gap-2 text-center">
                      <div>
                        <div className="text-lg font-bold tabular-nums">{scaledMacro.kcal}</div>
                        <div className="text-[10px] text-muted-foreground mt-0.5">kcal</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold tabular-nums text-blue-600">{scaledMacro.p}g</div>
                        <div className="text-[10px] text-muted-foreground mt-0.5">Proteine</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold tabular-nums text-amber-600">{scaledMacro.c}g</div>
                        <div className="text-[10px] text-muted-foreground mt-0.5">Carboidrati</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold tabular-nums text-rose-500">{scaledMacro.g}g</div>
                        <div className="text-[10px] text-muted-foreground mt-0.5">Grassi</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* CTA */}
                <Button
                  className="w-full h-11 text-base mt-auto"
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
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  ) : (
                    <Plus className="mr-2 h-5 w-5" />
                  )}
                  {replaceCompId != null ? "Sostituisci" : "Aggiungi al pasto"}
                </Button>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
