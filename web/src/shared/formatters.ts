export function formatCurrency(
  value: number | null | undefined,
  currency: string,
  options?: {
    digits?: number;
    compact?: boolean;
    locale?: string;
  },
) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "--";
  }

  const digits = options?.digits ?? 0;
  return new Intl.NumberFormat(options?.locale ?? "en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
    notation: options?.compact ? "compact" : "standard",
  }).format(value);
}

export function formatPercent(value: number | null, digits = 2) {
  if (value === null) {
    return "--";
  }

  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toFixed(digits)}%`;
}

export function formatNumber(value: number | null, digits = 0) {
  if (value === null) {
    return "--";
  }

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(value);
}

export function formatDateTime(value: string | null, locale = "zh-HK") {
  if (!value) {
    return "--";
  }

  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
