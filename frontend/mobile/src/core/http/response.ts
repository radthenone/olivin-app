export async function getResponseBody<TData>(
  response: Response,
): Promise<TData> {
  if (response.status === 204 || response.status === 205) {
    return undefined as TData;
  }

  const rawText = await response.text();

  if (!rawText) {
    return undefined as TData;
  }

  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    try {
      return JSON.parse(rawText) as TData;
    } catch {
      return rawText as TData;
    }
  }

  return rawText as TData;
}
