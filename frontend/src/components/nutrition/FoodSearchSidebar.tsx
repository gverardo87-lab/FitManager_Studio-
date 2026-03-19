// src/components/nutrition/FoodSearchSidebar.tsx
"use client";

/**
 * Food Selector — dialog professionale per ricerca e aggiunta alimenti.
 *
 * v3: redesign completo. Layout split con data-table a sinistra
 * e product card a destra. Tab categorie orizzontali.
 * Batch mode preservato (non chiude dopo aggiunta).
 */

import { useState, useEffect, useRef, useMemo } from "react";
import {
  Search,
  Loader2,
  Plus,
  Utensils,
  Check,
  Leaf,
  Beef,
  Milk,
  Wheat,
  CookingPot,
  Droplets,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import {
  useFoods,
  useAddComponent,
  useDeleteComponent,
  useFoodDetail,
  useNutritionCategories,
} from "@/hooks/useNutrition";
import type { Food } from "@/types/api";

// ── Category tabs ────────────────────────────────────────────────────────

interface CategoryTab {
  label: string;
  icon: typeof Utensils;
  categoryIds: number[];
}

const CATEGORY_TABS: CategoryTab[] = [
  { label: "Tutti", icon: Search, categoryIds: [] },
  { label: "Verdure e frutta", icon: Leaf, categoryIds: [5, 6, 7] },
  { label: "Carne e pesce", icon: Beef, categoryIds: [8, 9, 10, 11] },
  { label: "Latticini", icon: Milk, categoryIds: [12] },
  { label: "Cereali e pane", icon: Wheat, categoryIds: [1, 2, 3, 4] },
  { label: "Piatti pronti", icon: CookingPot, categoryIds: [16, 17, 18, 19, 20, 21] },
  { label: "Altro", icon: Droplets, categoryIds: [13, 14, 15] },
];

// ── Column header for food list ──────────────────────────────────────────

function ListHeader() {
  return (
    <div className="sticky top-0 z-10 flex items-center justify-between gap-3 border-b bg-background/95 backdrop-blur-sm px-5 py-2">
      <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
        Alimento
      </span>
      <div className="flex items-center gap-0 text-[11px] font-medium text-muted-foreground uppercase tracking-wider tabular-nums">
        <span className="w-[52px] text-right">kcal</span>
        <span className="w-[44px] text-right text-blue-500">Prot</span>
        <span className="w-[44px] text-right text-amber-500">Carb</span>
        <span className="w-[44px] text-right text-rose-400">Grassi</span>
      </div>
    </div>
  );
}

// ── Food row ─────────────────────────────────────────────────────────────

function FoodRow({
  food,
  isSelected,
  onSelect,
}: {
  food: Food;
  isSelected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      onClick={onSelect}
      aria-selected={isSelected}
      className={`group w-full flex items-center justify-between gap-3 px-5 py-3 text-left transition-all duration-150 border-b border-border/30 ${
        isSelected
          ? "bg-teal-50/70 dark:bg-teal-950/20 border-l-2 border-l-teal-500"
          : "hover:bg-muted/40 border-l-2 border-l-transparent"
      }`}
    >
      <div className="min-w-0 flex-1">
        <div
          className={`text-[13px] leading-tight truncate ${
            isSelected ? "font-semibold text-teal-900 dark:text-teal-100" : "font-medium"
          }`}
        >
          {food.nome}
        </div>
        {food.categoria_nome && (
          <div className="text-[11px] text-muted-foreground/50 mt-0.5 truncate">
            {food.categoria_nome}
          </div>
        )}
      </div>
      <div className="flex items-center gap-0 text-[12px] tabular-nums shrink-0">
        <span className="w-[52px] text-right font-semibold text-foreground/70">
          {Math.round(food.energia_kcal)}
        </span>
        <span className="w-[44px] text-right font-medium text-blue-600 dark:text-blue-400">
          {food.proteine_g}
        </span>
        <span className="w-[44px] text-right font-medium text-amber-600 dark:text-amber-400">
          {food.carboidrati_g}
        </span>
        <span className="w-[44px] text-right font-medium text-rose-500 dark:text-rose-400">
          {food.grassi_g}
        </span>
      </div>
    </button>
  );
}

// ── Macro pill (used in detail panel) ────────────────────────────────────

function MacroPill({
  value,
  label,
  color,
  large,
}: {
  value: string | number;
  label: string;
  color: string;
  large?: boolean;
}) {
  return (
    <div className={`flex flex-col items-center gap-0.5 ${large ? "flex-1" : ""}`}>
      <span
        className={`tabular-nums font-bold ${color} ${
          large ? "text-2xl" : "text-base"
        }`}
      >
        {value}
      </span>
      <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
        {label}
      </span>
    </div>
  );
}

// ── Props ─────────────────────────────────────────────────────────────────

interface FoodSearchSidebarProps {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  planId: number;
  mealId: number | null;
  mealLabel?: string;
  replaceCompId?: number | null;
}

// ── Main component ───────────────────────────────────────────────────────

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
  useNutritionCategories(); // pre-warm cache

  const activeCategoryIds = CATEGORY_TABS[activeTabIdx]?.categoryIds ?? [];
  const categoryIdParam =
    activeCategoryIds.length === 1 ? activeCategoryIds[0] : undefined;

  const { data: rawFoods = [], isLoading } = useFoods(
    debouncedQuery || undefined,
    categoryIdParam,
  );

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

  const handleAdd = async () => {
    if (!selectedFood || mealId === null) return;
    const g = parseFloat(quantita);
    if (!g || g <= 0) return;

    if (replaceCompId != null) {
      await deleteComponent.mutateAsync({
        planId,
        mealId,
        compId: replaceCompId,
      });
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
  const scaledMacro =
    selectedFood && qty > 0
      ? {
          kcal: Math.round((selectedFood.energia_kcal * qty) / 100),
          p:
            Math.round(
              ((selectedFood.proteine_g * qty) / 100) * 10,
            ) / 10,
          c:
            Math.round(
              ((selectedFood.carboidrati_g * qty) / 100) * 10,
            ) / 10,
          g:
            Math.round(((selectedFood.grassi_g * qty) / 100) * 10) /
            10,
        }
      : null;

  const headerTitle =
    replaceCompId != null
      ? "Sostituisci alimento"
      : mealLabel
        ? `Aggiungi a ${mealLabel}`
        : "Aggiungi alimento";

  const isPending = addComponent.isPending || deleteComponent.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[1100px] h-[82vh] flex flex-col gap-0 p-0 overflow-hidden rounded-2xl overscroll-contain">
        {/* ── Header ── */}
        <DialogHeader className="px-6 pt-5 pb-0 shrink-0">
          <div className="flex items-center justify-between">
            <DialogTitle className="flex items-center gap-2 text-base font-semibold">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-teal-100 dark:bg-teal-900/40">
                <Utensils className="h-3.5 w-3.5 text-teal-700 dark:text-teal-300" />
              </div>
              {headerTitle}
            </DialogTitle>
            {addedCount > 0 && (
              <span className="flex items-center gap-1.5 rounded-full bg-emerald-50 border border-emerald-200/60 px-3 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-950/30 dark:border-emerald-800 dark:text-emerald-300">
                <Check className="h-3 w-3" />
                {addedCount}
              </span>
            )}
          </div>
        </DialogHeader>

        {/* ── Search bar ── */}
        <div className="px-6 pt-4 pb-3 shrink-0">
          <div className="relative">
            <Search className="absolute left-3.5 top-3 h-4 w-4 text-muted-foreground/60" />
            <Input
              ref={searchRef}
              placeholder="Cerca per nome…"
              aria-label="Cerca alimento per nome"
              autoComplete="off"
              className="pl-10 h-10 text-sm rounded-xl bg-muted/40 border-0 focus-visible:ring-1 focus-visible:ring-teal-500/40"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
        </div>

        {/* ── Category tabs ── */}
        <div className="px-6 pb-4 shrink-0">
          <div className="flex gap-1.5" role="tablist" aria-label="Categorie alimentari">
            {CATEGORY_TABS.map((tab, idx) => {
              const Icon = tab.icon;
              const isActive = activeTabIdx === idx;
              return (
                <button
                  key={tab.label}
                  role="tab"
                  aria-selected={isActive}
                  onClick={() => setActiveTabIdx(idx)}
                  className={`flex items-center gap-1.5 whitespace-nowrap rounded-lg px-3 py-1.5 text-[13px] font-medium transition-all duration-150 ${
                    isActive
                      ? "bg-teal-600 text-white shadow-sm shadow-teal-600/20"
                      : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                  }`}
                >
                  <Icon className={`h-3.5 w-3.5 ${isActive ? "text-white/80" : "text-muted-foreground/60"}`} />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* ── Body: split panel ── */}
        <div className="flex-1 flex min-h-0 border-t">
          {/* LEFT: food list (62%) */}
          <div className="w-[62%] shrink-0 min-h-0 overflow-hidden border-r">
            <ScrollArea className="h-full">
              <ListHeader />
              {isLoading && (
                <div className="flex items-center justify-center py-24">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground/40" />
                </div>
              )}
              {!isLoading && !hasQuery && (
                <div className="flex flex-col items-center justify-center py-24 px-8">
                  <div className="h-12 w-12 rounded-2xl bg-muted/50 flex items-center justify-center mb-4">
                    <Search className="h-5 w-5 text-muted-foreground/30" />
                  </div>
                  <p className="text-sm text-muted-foreground/60 text-center">
                    Cerca per nome o seleziona una categoria
                  </p>
                </div>
              )}
              {!isLoading && hasQuery && foods.length === 0 && (
                <div className="flex flex-col items-center justify-center py-24">
                  <p className="text-sm text-muted-foreground/60">
                    Nessun alimento trovato
                  </p>
                </div>
              )}
              {!isLoading &&
                foods.map((food) => (
                  <FoodRow
                    key={food.id}
                    food={food}
                    isSelected={selectedFood?.id === food.id}
                    onSelect={() => handleSelect(food)}
                  />
                ))}
            </ScrollArea>
          </div>

          {/* RIGHT: detail panel (38%) */}
          <div className="w-[38%] shrink-0 flex flex-col min-h-0 bg-muted/5">
            {!selectedFood ? (
              /* Empty state */
              <div className="flex-1 flex flex-col items-center justify-center px-8">
                <div className="h-16 w-16 rounded-2xl bg-muted/30 flex items-center justify-center mb-4">
                  <Utensils className="h-7 w-7 text-muted-foreground/20" />
                </div>
                <p className="text-sm text-muted-foreground/50 text-center leading-relaxed">
                  Seleziona un alimento
                  <br />
                  dalla lista
                </p>
              </div>
            ) : (
              /* Detail card */
              <div className="flex-1 flex flex-col overflow-y-auto">
                {/* Food identity */}
                <div className="px-6 pt-6 pb-5">
                  <h3 className="text-lg font-bold leading-snug tracking-tight">
                    {selectedFood.nome}
                  </h3>
                  {selectedFood.categoria_nome && (
                    <span className="inline-block mt-2 rounded-md bg-muted/60 px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
                      {selectedFood.categoria_nome}
                    </span>
                  )}

                  {/* Macro per 100g — subtle */}
                  <div className="mt-4 flex items-end gap-4">
                    <MacroPill
                      value={Math.round(selectedFood.energia_kcal)}
                      label="kcal"
                      color="text-foreground/70"
                    />
                    <MacroPill
                      value={`${selectedFood.proteine_g}g`}
                      label="Prot"
                      color="text-blue-600 dark:text-blue-400"
                    />
                    <MacroPill
                      value={`${selectedFood.carboidrati_g}g`}
                      label="Carb"
                      color="text-amber-600 dark:text-amber-400"
                    />
                    <MacroPill
                      value={`${selectedFood.grassi_g}g`}
                      label="Grassi"
                      color="text-rose-500 dark:text-rose-400"
                    />
                  </div>
                  <p className="text-[10px] text-muted-foreground/40 mt-1.5">
                    valori per 100g
                  </p>
                </div>

                {/* Divider */}
                <div className="mx-6 h-px bg-border/60" />

                {/* Quantity section */}
                <div className="px-6 py-5 space-y-3">
                  <label htmlFor="food-qty-input" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Quantità (grammi)
                  </label>
                  <Input
                    id="food-qty-input"
                    type="number"
                    min={1}
                    max={2000}
                    autoComplete="off"
                    autoFocus
                    value={quantita}
                    onChange={(e) => setQuantita(e.target.value)}
                    className="text-center tabular-nums h-12 text-xl font-bold rounded-xl border-2 focus-visible:border-teal-500 focus-visible:ring-0"
                  />
                  <div className="flex flex-wrap gap-1.5 justify-center">
                    {(foodDetail?.porzioni?.length
                      ? foodDetail.porzioni.slice(0, 6).map((p) => ({
                          key: String(p.id),
                          label: p.nome,
                          sub: `${p.grammi}g`,
                          grams: p.grammi,
                        }))
                      : [50, 80, 100, 150, 200, 250].map((gVal) => ({
                          key: String(gVal),
                          label: `${gVal}g`,
                          sub: "",
                          grams: gVal,
                        }))
                    ).map((item) => {
                      const isActive = quantita === String(item.grams);
                      return (
                        <button
                          key={item.key}
                          type="button"
                          onClick={() => setQuantita(String(item.grams))}
                          className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-all duration-150 ${
                            isActive
                              ? "border-teal-500 bg-teal-50 text-teal-700 dark:bg-teal-950/30 dark:text-teal-300 dark:border-teal-700"
                              : "border-border/60 text-muted-foreground hover:border-teal-400/50 hover:text-foreground"
                          }`}
                        >
                          {item.label}
                          {item.sub && (
                            <span className="ml-1 text-[10px] opacity-60">
                              {item.sub}
                            </span>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Scaled macro result — the hero */}
                {scaledMacro && (
                  <div className="mx-6 mb-4 rounded-xl bg-gradient-to-br from-teal-50 to-emerald-50/60 dark:from-teal-950/40 dark:to-emerald-950/20 border border-teal-200/40 dark:border-teal-800/30 p-5">
                    <p className="text-[10px] font-bold text-teal-700/60 dark:text-teal-400/60 uppercase tracking-widest mb-3">
                      Per {quantita}g
                    </p>
                    <div className="flex items-end justify-between">
                      <MacroPill
                        value={scaledMacro.kcal}
                        label="kcal"
                        color="text-foreground"
                        large
                      />
                      <MacroPill
                        value={`${scaledMacro.p}g`}
                        label="Prot"
                        color="text-blue-600 dark:text-blue-400"
                        large
                      />
                      <MacroPill
                        value={`${scaledMacro.c}g`}
                        label="Carb"
                        color="text-amber-600 dark:text-amber-400"
                        large
                      />
                      <MacroPill
                        value={`${scaledMacro.g}g`}
                        label="Grassi"
                        color="text-rose-500 dark:text-rose-400"
                        large
                      />
                    </div>
                  </div>
                )}

                {/* CTA — pinned bottom */}
                <div className="mt-auto px-6 py-4 border-t bg-background/80 backdrop-blur-sm">
                  <Button
                    className="w-full h-11 rounded-xl text-sm font-semibold bg-teal-600 hover:bg-teal-700 text-white shadow-sm shadow-teal-600/20"
                    onClick={handleAdd}
                    disabled={
                      isPending ||
                      !quantita ||
                      parseFloat(quantita) <= 0 ||
                      mealId === null
                    }
                  >
                    {isPending ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Plus className="mr-2 h-4 w-4" />
                    )}
                    {replaceCompId != null
                      ? "Sostituisci"
                      : "Aggiungi al pasto"}
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
