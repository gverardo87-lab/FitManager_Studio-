// src/components/ui/whatsapp-button.tsx
"use client";

/**
 * Bottone WhatsApp riusabile — apre wa.me con messaggio pre-compilato.
 *
 * Varianti:
 * - "icon": solo icona (per spazi stretti: rate card, hover card)
 * - "compact": icona + "WhatsApp" (per sezioni contatti)
 * - "full": icona + label personalizzata (per azioni esplicite)
 */

import { Button } from "@/components/ui/button";
import { buildWhatsAppUrl } from "@/lib/format";
import { cn } from "@/lib/utils";
import { useLogCommunication } from "@/hooks/useCommunications";

// SVG inline — lucide-react non ha l'icona WhatsApp
function WhatsAppIcon({ className }: { className?: string }) {
  return (
    <svg
      role="img"
      aria-label="WhatsApp"
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
    >
      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
    </svg>
  );
}

type WhatsAppVariant = "icon" | "compact" | "full";

interface WhatsAppButtonProps {
  phone: string | null | undefined;
  message?: string;
  variant?: WhatsAppVariant;
  label?: string;
  className?: string;
  /** Se fornito, il click logga la comunicazione nel CRM. */
  clientId?: number;
  /** Chiave del template usato (es. 'birthday', 'checkin'). */
  templateKey?: string;
}

export function WhatsAppButton({
  phone,
  message,
  variant = "icon",
  label,
  className,
  clientId,
  templateKey,
}: WhatsAppButtonProps) {
  const url = buildWhatsAppUrl(phone, message);
  const logComm = useLogCommunication();
  if (!url) return null;

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    window.open(url, "_blank", "noopener,noreferrer");
    // Log trasparente — non blocca l'utente
    if (clientId) {
      logComm.mutate({
        id_cliente: clientId,
        canale: "whatsapp",
        template_usato: templateKey,
        anteprima: (message ?? "").slice(0, 200),
      });
    }
  };

  // Variante icon: usa <a> nativo invece di <Button> per evitare
  // button-inside-button (hydration error in SessionItem, EventHoverCard, etc.)
  if (variant === "icon") {
    return (
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        onClick={handleClick}
        title="Contatta su WhatsApp"
        className={cn(
          "inline-flex items-center justify-center rounded-md transition-colors",
          "h-7 w-7 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 dark:text-emerald-400 dark:hover:bg-emerald-950/30",
          className,
        )}
      >
        <WhatsAppIcon className="h-3.5 w-3.5" />
      </a>
    );
  }

  return (
    <Button
      variant="outline"
      size="sm"
      className={cn(
        "gap-1.5 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 border-emerald-200 dark:text-emerald-400 dark:hover:bg-emerald-950/30 dark:border-emerald-800",
        variant === "compact" && "h-7 text-xs",
        className,
      )}
      onClick={handleClick}
    >
      <WhatsAppIcon className="h-3.5 w-3.5" />
      {label ?? "WhatsApp"}
    </Button>
  );
}
