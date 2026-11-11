import { describe, expect, test } from "bun:test";

import {
  handleRevalidateRequest,
  parseRevalidatePayload,
  verifyRevalidateSecret,
} from "./revalidate";

describe("verifyRevalidateSecret", () => {
  test("rejects missing or empty secret", () => {
    expect(verifyRevalidateSecret(null, "secret123")).toBe(false);
    expect(verifyRevalidateSecret("", "secret123")).toBe(false);
    expect(verifyRevalidateSecret("secret123", undefined)).toBe(false);
    expect(verifyRevalidateSecret("secret123", "")).toBe(false);
    expect(verifyRevalidateSecret(undefined, undefined)).toBe(false);
  });

  test("rejects mismatched secret with same or different length", () => {
    expect(verifyRevalidateSecret("secret123", "secret124")).toBe(false);
    expect(verifyRevalidateSecret("secret12", "secret12345")).toBe(false);
    expect(verifyRevalidateSecret("secret12345", "secret12")).toBe(false);
  });

  test("accepts matching secret", () => {
    expect(
      verifyRevalidateSecret("super-secret-token", "super-secret-token"),
    ).toBe(true);
  });
});

describe("parseRevalidatePayload", () => {
  test("rejects non-object payloads", () => {
    expect(parseRevalidatePayload(null).ok).toBe(false);
    expect(parseRevalidatePayload("string").ok).toBe(false);
    expect(parseRevalidatePayload(123).ok).toBe(false);
    expect(parseRevalidatePayload(["tag"]).ok).toBe(false);
  });

  test("rejects payload without tags array or with empty tags", () => {
    expect(parseRevalidatePayload({}).ok).toBe(false);
    expect(parseRevalidatePayload({ tags: "not-an-array" }).ok).toBe(false);
    expect(parseRevalidatePayload({ tags: [] }).ok).toBe(false);
  });

  test("rejects tags containing non-string or blank items", () => {
    expect(parseRevalidatePayload({ tags: [123] }).ok).toBe(false);
    expect(parseRevalidatePayload({ tags: [null] }).ok).toBe(false);
    expect(parseRevalidatePayload({ tags: [""] }).ok).toBe(false);
    expect(parseRevalidatePayload({ tags: ["   "] }).ok).toBe(false);
    expect(parseRevalidatePayload({ tags: ["valid", ""] }).ok).toBe(false);
  });

  test("rejects too many tags or too long tag", () => {
    const tooMany = Array.from({ length: 101 }, (_, i) => `t${i}`);
    expect(parseRevalidatePayload({ tags: tooMany }).ok).toBe(false);
    expect(parseRevalidatePayload({ tags: tooMany.slice(0, 100) }).ok).toBe(
      true,
    );
    expect(parseRevalidatePayload({ tags: ["a".repeat(257)] }).ok).toBe(false);
    expect(parseRevalidatePayload({ tags: ["a".repeat(256)] }).ok).toBe(true);
  });

  test("accepts valid tags array", () => {
    const result = parseRevalidatePayload({
      tags: ["product:ring", "catalog"],
    });
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.tags).toEqual(["product:ring", "catalog"]);
    }
  });
});

describe("handleRevalidateRequest", () => {
  const secret = "correct-secret";

  test("returns 401 when secret header is missing or invalid", async () => {
    const noSecretRequest = new Request("http://localhost/api/revalidate", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ tags: ["catalog"] }),
    });
    const res1 = await handleRevalidateRequest(noSecretRequest, { secret });
    expect(res1.status).toBe(401);

    const wrongSecretRequest = new Request("http://localhost/api/revalidate", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-revalidate-secret": "wrong",
      },
      body: JSON.stringify({ tags: ["catalog"] }),
    });
    const res2 = await handleRevalidateRequest(wrongSecretRequest, { secret });
    expect(res2.status).toBe(401);
  });

  test("returns 400 when body is invalid JSON or has invalid tags", async () => {
    const invalidJsonRequest = new Request("http://localhost/api/revalidate", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-revalidate-secret": secret,
      },
      body: "invalid json",
    });
    const res1 = await handleRevalidateRequest(invalidJsonRequest, { secret });
    expect(res1.status).toBe(400);

    const invalidTagsRequest = new Request("http://localhost/api/revalidate", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-revalidate-secret": secret,
      },
      body: JSON.stringify({ tags: [] }),
    });
    const res2 = await handleRevalidateRequest(invalidTagsRequest, { secret });
    expect(res2.status).toBe(400);
  });

  test("returns 200 and revalidates every tag when authorized", async () => {
    const revalidated: string[] = [];
    const request = new Request("http://localhost/api/revalidate", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-revalidate-secret": secret,
      },
      body: JSON.stringify({ tags: ["product:ring", "catalog"] }),
    });

    const response = await handleRevalidateRequest(request, {
      secret,
      revalidateTagFn: (tag) => {
        revalidated.push(tag);
      },
    });

    expect(response.status).toBe(200);
    expect(revalidated).toEqual(["product:ring", "catalog"]);
    const json = (await response.json()) as {
      revalidated: boolean;
      tags: string[];
    };
    expect(json.revalidated).toBe(true);
    expect(json.tags).toEqual(["product:ring", "catalog"]);
  });
});
