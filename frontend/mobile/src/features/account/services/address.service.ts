import {
  customersAddressesCreate,
  customersAddressesDestroy,
  customersAddressesList,
  customersAddressesPartialUpdate,
  customersAddressesSetDefaultPartialUpdate,
} from "@api/generated/apps/addresses/addresses";
import type { Address, PatchedAddress } from "@api/generated/apps/schemas";

export type AddressCreateInput = Omit<Address, "id">;
export type AddressUpdateInput = {
  id: string;
  data: PatchedAddress;
};

/**
 * Serwis adresów aktualnego użytkownika.
 *
 * Dlaczego istnieje:
 * adresy należą do konta użytkownika i są server state. Hooki używają
 * tego serwisu zamiast wołać wygenerowane funkcje API bezpośrednio.
 */
export const addressService = {
  async list() {
    const response = await customersAddressesList();
    return response.data;
  },

  async create(data: AddressCreateInput) {
    const response = await customersAddressesCreate(data as Address);
    return response.data;
  },

  async update({ id, data }: AddressUpdateInput) {
    const response = await customersAddressesPartialUpdate(id, data);
    return response.data;
  },

  async remove(id: string) {
    await customersAddressesDestroy(id);
  },

  async setDefault(id: string) {
    const response = await customersAddressesSetDefaultPartialUpdate(id, {});
    return response.data;
  },
};
