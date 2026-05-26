import { useMutation, useQueryClient } from "@tanstack/react-query";
import { accountQueryKeys } from "../constants/account-query-keys";
import { addressService } from "../services/address.service";

/**
 * Usuwa adres użytkownika i odświeża listę adresów.
 */
export function useDeleteAddress() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: addressService.remove,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: accountQueryKeys.addresses(),
      });
    },
  });
}
