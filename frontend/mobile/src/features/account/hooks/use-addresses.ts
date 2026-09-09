import { useQuery } from "@tanstack/react-query";
import { accountQueryKeys } from "../constants/account-query-keys";
import { addressService } from "../services/address.service";

/**
 * Pobiera adresy aktualnego użytkownika.
 */
export function useAddresses() {
  return useQuery({
    queryKey: accountQueryKeys.addresses(),
    queryFn: addressService.list,
  });
}
