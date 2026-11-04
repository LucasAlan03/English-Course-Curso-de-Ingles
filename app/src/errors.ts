type ErrorLike = { code?: string; detail?: string; provider?: string };

/** A friendly Portuguese message for any error thrown by the api client. */
export function describeError(error: unknown): string {
  const e = (error ?? {}) as ErrorLike;
  const who = e.provider ?? 'um provedor';
  switch (e.code) {
    case 'provider_out_of_credit':
      return `Os créditos de ${who} acabaram. Recarregue no console dele ou volte para o perfil gratuito.`;
    case 'provider_rate_limited':
      return `${who} atingiu o limite de requisições. Aguarde um pouco ou ative o perfil pago.`;
    case 'monthly_cap_reached':
      return 'O teto mensal de gastos foi atingido. Aumente MONTHLY_CAP_BRL ou espere o próximo mês.';
    case 'invalid_ai_output':
      return 'A IA devolveu uma resposta inválida. Tente de novo.';
    case 'empty_transcript':
      return 'Não consegui ouvir nada. Repita, por favor.';
    case 'provider_unavailable':
      return `${who} está fora do ar ou sobrecarregado agora. Tente de novo em instantes.`;
    case 'provider_auth_failed':
      return `A chave de API de ${who} está ausente ou inválida. Confira o .env do backend.`;
    case 'finish_in_progress':
      return 'O relatório já está sendo gerado. Aguarde alguns segundos e tente de novo.';
    case 'internal_error':
      return 'Erro inesperado no servidor. Veja o terminal do backend e tente de novo.';
    default:
      return e.detail || String(error);
  }
}
