import { beforeEach, describe, expect, mock, test } from "bun:test";

let mockProfilesListResponse: any = {
  data: { results: [{ id: "prof-1", deliveryCountry: null }] },
};
let lastPatchPayload: any = null;
let patchShouldThrow = false;

mock.module("@olivin/api/generated/apps/profiles/profiles", () => ({
  customersProfileList: async () => mockProfilesListResponse,
  customersProfilePartialUpdate: async (id: string, body: any) => {
    if (patchShouldThrow) {
      throw new Error("Network error");
    }
    lastPatchPayload = { id, body };
    return { data: { id, ...body }, status: 200 };
  },
}));

// Podstawiamy globalny obiekt document dla ciasteczek
let cookieJar = "";
const fakeDocument = {
  get cookie() {
    return cookieJar;
  },
  set cookie(val: string) {
    // Prosta symulacja: usuń wcześniejszy klucz, dodaj nową parę
    const [nameVal] = val.split(";");
    const [name] = nameVal.split("=");
    const cookies = cookieJar
      .split("; ")
      .filter((c) => c && !c.startsWith(`${name}=`));
    cookies.push(nameVal);
    cookieJar = cookies.join("; ");
  },
};

(globalThis as any).document = fakeDocument;
(globalThis as any).location = { protocol: "http:" };

const {
  saveDeliveryCountryCookie,
  readDeliveryCountryCookie,
  saveProfileDeliveryCountry,
  syncDeliveryCountryOnLogin,
} = await import("./profile-delivery-country");

describe("profile-delivery-country", () => {
  beforeEach(() => {
    cookieJar = "";
    lastPatchPayload = null;
    patchShouldThrow = false;
    mockProfilesListResponse = {
      data: { results: [{ id: "prof-1", deliveryCountry: null }] },
    };
  });

  describe("cookie helpers", () => {
    test("zapisuje i odczytuje poprawny kraj dostawy", () => {
      expect(readDeliveryCountryCookie()).toBeNull();
      saveDeliveryCountryCookie("DE");
      expect(readDeliveryCountryCookie()).toBe("DE");
    });

    test("ignoruje nieprawidłowe lub nieunijne kraje przy odczycie", () => {
      cookieJar = "delivery_country=US";
      expect(readDeliveryCountryCookie()).toBeNull();
    });
  });

  describe("saveProfileDeliveryCountry", () => {
    test("aktualizuje profil zalogowanego użytkownika", async () => {
      mockProfilesListResponse = {
        data: { results: [{ id: "prof-42", deliveryCountry: "PL" }] },
      };

      await saveProfileDeliveryCountry("DE");

      expect(lastPatchPayload).toEqual({
        id: "prof-42",
        body: { deliveryCountry: "DE" },
      });
    });

    test("rzuca błąd, gdy brak profilu w odpowiedzi API", async () => {
      mockProfilesListResponse = {
        data: { results: [] },
      };

      expect(saveProfileDeliveryCountry("DE")).rejects.toThrow(
        "Nie znaleziono profilu klienta.",
      );
    });
  });

  describe("syncDeliveryCountryOnLogin", () => {
    test("kraj z profilu nadpisuje cookie, gdy profil ma wartość", async () => {
      saveDeliveryCountryCookie("PL");
      mockProfilesListResponse = {
        data: { results: [{ id: "prof-1", deliveryCountry: "DE" }] },
      };

      const result = await syncDeliveryCountryOnLogin();

      expect(result).toEqual({ country: "DE", source: "profile" });
      expect(readDeliveryCountryCookie()).toBe("DE");
      // Nie powinno być zapisu do profilu, bo to profil wygrał
      expect(lastPatchPayload).toBeNull();
    });

    test("pusty profil przejmuje wartość z cookie", async () => {
      saveDeliveryCountryCookie("FR");
      mockProfilesListResponse = {
        data: { results: [{ id: "prof-1", deliveryCountry: null }] },
      };

      const result = await syncDeliveryCountryOnLogin();

      expect(result).toEqual({ country: "FR", source: "cookie" });
      expect(readDeliveryCountryCookie()).toBe("FR");
      expect(lastPatchPayload).toEqual({
        id: "prof-1",
        body: { deliveryCountry: "FR" },
      });
    });

    test("błąd zapisu pustego profilu nie cofa wyboru w cookie", async () => {
      saveDeliveryCountryCookie("IT");
      patchShouldThrow = true;
      mockProfilesListResponse = {
        data: { results: [{ id: "prof-1", deliveryCountry: null }] },
      };

      const result = await syncDeliveryCountryOnLogin();

      expect(result).toEqual({ country: "IT", source: "cookie" });
      expect(readDeliveryCountryCookie()).toBe("IT");
    });

    test("gdy brak cookie i profil pusty, nic nie zmienia", async () => {
      mockProfilesListResponse = {
        data: { results: [{ id: "prof-1", deliveryCountry: null }] },
      };

      const result = await syncDeliveryCountryOnLogin();

      expect(result).toEqual({ country: null, source: "none" });
      expect(readDeliveryCountryCookie()).toBeNull();
      expect(lastPatchPayload).toBeNull();
    });
  });
});
