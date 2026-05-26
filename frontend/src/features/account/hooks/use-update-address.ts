import { useMutation, useQueryClient } from "@tanstack/react-query";
import { accountQueryKeys } from "../constants/account-query-keys";
import { addressService } from "../services/address.service";

/**
 * Aktualizuje adres użytkownika i odświeża cache konta.
 */
export function useUpdateAddress() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: addressService.update,
    onSuccess: async (address) => {
      await queryClient.invalidateQueries({
        queryKey: accountQueryKeys.addresses(),
      });
      await queryClient.invalidateQueries({
        queryKey: accountQueryKeys.address(address.id),
      });
    },
  });
}
