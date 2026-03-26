// src/components/agenda/TodoHoverCard.tsx
"use client";

/**
 * Popover per promemoria nel calendario.
 *
 * Si apre al CLICK (non hover) perche' i promemoria sono banner all-day piccoli.
 * Azioni: toggle completato, modifica titolo inline, elimina.
 *
 * Usa createPortal come EventHoverCard (escape .rbc-event overflow:hidden).
 */

import { useState, useRef, useCallback, useEffect, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { format } from "date-fns";
import { it } from "date-fns/locale";
import {
  CheckCircle2,
  Circle,
  Pencil,
  Trash2,
  StickyNote,
  CalendarDays,
  X,
  Check,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { useToggleTodo, useUpdateTodo, useDeleteTodo } from "@/hooks/useTodos";
import type { Todo } from "@/types/api";

interface TodoHoverCardProps {
  todo: Todo;
  children: ReactNode;
}

export function TodoHoverCard({ todo, children }: TodoHoverCardProps) {
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(todo.titolo);
  const [position, setPosition] = useState<{ top: number; left: number } | null>(null);
  const triggerRef = useRef<HTMLDivElement>(null);
  const popupRef = useRef<HTMLDivElement>(null);

  const toggleTodo = useToggleTodo();
  const updateTodo = useUpdateTodo();
  const deleteTodo = useDeleteTodo();

  const calculatePosition = useCallback(() => {
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    const popupWidth = 280;
    let left = rect.left + rect.width / 2 - popupWidth / 2;
    left = Math.max(8, Math.min(left, window.innerWidth - popupWidth - 8));
    const top = rect.bottom + 4;
    setPosition({ top, left });
  }, []);

  const handleOpen = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      calculatePosition();
      setOpen(true);
      setEditing(false);
      setEditTitle(todo.titolo);
    },
    [calculatePosition, todo.titolo]
  );

  const handleClose = useCallback(() => {
    setOpen(false);
    setPosition(null);
    setEditing(false);
  }, []);

  // Chiudi su click esterno o ESC
  useEffect(() => {
    if (!open) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (
        popupRef.current &&
        !popupRef.current.contains(e.target as Node) &&
        triggerRef.current &&
        !triggerRef.current.contains(e.target as Node)
      ) {
        handleClose();
      }
    };
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") handleClose();
    };
    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEsc);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEsc);
    };
  }, [open, handleClose]);

  // Riposiziona su scroll/resize
  useEffect(() => {
    if (!open) return;
    const sync = () => calculatePosition();
    window.addEventListener("resize", sync);
    window.addEventListener("scroll", sync, true);
    return () => {
      window.removeEventListener("resize", sync);
      window.removeEventListener("scroll", sync, true);
    };
  }, [open, calculatePosition]);

  const handleToggle = useCallback(() => {
    toggleTodo.mutate(todo.id);
    handleClose();
  }, [toggleTodo, todo.id, handleClose]);

  const handleSaveEdit = useCallback(() => {
    const trimmed = editTitle.trim();
    if (trimmed && trimmed !== todo.titolo) {
      updateTodo.mutate({ id: todo.id, titolo: trimmed });
    }
    setEditing(false);
  }, [editTitle, todo.id, todo.titolo, updateTodo]);

  const handleDelete = useCallback(() => {
    deleteTodo.mutate(todo.id);
    handleClose();
  }, [deleteTodo, todo.id, handleClose]);

  // Urgenza colore data
  const today = format(new Date(), "yyyy-MM-dd");
  const isOverdue = !!todo.data_scadenza && todo.data_scadenza < today && !todo.completato;
  const isToday = todo.data_scadenza === today && !todo.completato;

  const dateBadgeClass = isOverdue
    ? "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300"
    : isToday
      ? "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300"
      : "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300";

  return (
    <>
      <div ref={triggerRef} onClick={handleOpen} className="cursor-pointer">
        {children}
      </div>

      {open && position && createPortal(
        <div
          ref={popupRef}
          className="fixed z-[9999]"
          style={{ top: position.top, left: position.left }}
        >
          <div className="w-[280px] rounded-xl border bg-popover p-3.5 shadow-lg animate-in fade-in-0 zoom-in-95 duration-150">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <StickyNote className="h-3.5 w-3.5 text-amber-500" />
                <span className="text-xs font-semibold text-amber-700 dark:text-amber-300">
                  Promemoria
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                    todo.completato
                      ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300"
                      : dateBadgeClass
                  }`}
                >
                  {todo.completato ? "Completato" : isOverdue ? "Scaduto" : isToday ? "Oggi" : "Da fare"}
                </span>
                <button
                  type="button"
                  onClick={handleClose}
                  className="rounded p-0.5 text-muted-foreground/60 hover:text-muted-foreground"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            {/* Titolo (editabile inline) */}
            {editing ? (
              <div className="mt-2 flex items-center gap-1.5">
                <Input
                  autoFocus
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleSaveEdit();
                    if (e.key === "Escape") setEditing(false);
                  }}
                  className="h-7 text-sm"
                  maxLength={200}
                />
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 shrink-0 p-0 text-emerald-600"
                  onClick={handleSaveEdit}
                >
                  <Check className="h-3.5 w-3.5" />
                </Button>
              </div>
            ) : (
              <p
                className={`mt-1.5 text-sm font-medium leading-tight ${
                  todo.completato ? "line-through opacity-60" : ""
                }`}
              >
                {todo.titolo}
              </p>
            )}

            {/* Data */}
            {todo.data_scadenza && (
              <div className="mt-1.5 flex items-center gap-1.5 text-xs text-muted-foreground">
                <CalendarDays className="h-3 w-3" />
                <span className="capitalize">
                  {format(new Date(todo.data_scadenza + "T00:00:00"), "EEEE d MMMM yyyy", { locale: it })}
                </span>
              </div>
            )}

            {/* Descrizione */}
            {todo.descrizione && (
              <p className="mt-1.5 truncate text-[11px] text-muted-foreground/80 italic">
                {todo.descrizione}
              </p>
            )}

            {/* Azioni */}
            <Separator className="my-2.5" />
            <div className="flex gap-1.5">
              <Button
                variant="outline"
                size="sm"
                className={`h-7 flex-1 gap-1 text-[11px] ${
                  todo.completato
                    ? "text-blue-600 hover:text-blue-700 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-950/30"
                    : "text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 dark:text-emerald-400 dark:hover:bg-emerald-950/30"
                }`}
                onClick={handleToggle}
              >
                {todo.completato ? (
                  <><Circle className="h-3 w-3" />Riapri</>
                ) : (
                  <><CheckCircle2 className="h-3 w-3" />Completa</>
                )}
              </Button>
              {!editing && (
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 flex-1 gap-1 text-[11px] text-zinc-600 hover:text-zinc-700 hover:bg-zinc-50 dark:text-zinc-400 dark:hover:bg-zinc-800"
                  onClick={() => {
                    setEditing(true);
                    setEditTitle(todo.titolo);
                  }}
                >
                  <Pencil className="h-3 w-3" />
                  Modifica
                </Button>
              )}
              <Button
                variant="outline"
                size="sm"
                className="h-7 w-8 shrink-0 p-0 text-[11px] text-red-500 hover:text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/30"
                onClick={handleDelete}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  );
}
