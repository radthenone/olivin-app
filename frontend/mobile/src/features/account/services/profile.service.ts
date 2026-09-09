import {
  customersProfileCreate,
  customersProfileList,
  customersProfilePartialUpdate,
} from "@api/generated/apps/profiles/profiles";
import type { PatchedProfile, Profile } from "@api/generated/apps/schemas";

export type ProfileRequiredData = {
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  phoneNumber: string;
};

export type ProfileEditableData = {
  firstName: string;
  lastName: string;
  phoneNumber: string;
};

export function isProfileComplete(profile?: Profile | null) {
  return Boolean(
    profile?.firstName?.trim() &&
    profile.lastName?.trim() &&
    profile.dateOfBirth &&
    profile.phoneNumber?.trim(),
  );
}

/**
 * Serwis profilu aktualnego użytkownika.
 *
 * Dlaczego istnieje:
 * ekrany i hooki nie powinny importować Orvala bezpośrednio ani znać
 * szczegółu, że backend zwraca profil użytkownika jako jednoelementową listę.
 */
export const profileService = {
  async getCurrentProfile() {
    const response = await customersProfileList();
    return response.data[0] ?? null;
  },

  async saveRequiredData(data: ProfileRequiredData) {
    const currentProfile = await profileService.getCurrentProfile();
    const payload: PatchedProfile = {
      firstName: data.firstName.trim(),
      lastName: data.lastName.trim(),
      dateOfBirth: data.dateOfBirth,
      phoneNumber: data.phoneNumber.trim(),
    };

    if (currentProfile?.id) {
      const response = await customersProfilePartialUpdate(
        currentProfile.id,
        payload,
      );
      return response.data;
    }

    const response = await customersProfileCreate(payload as Profile);
    return response.data;
  },

  async saveEditableData(data: ProfileEditableData) {
    const currentProfile = await profileService.getCurrentProfile();
    const payload: PatchedProfile = {
      firstName: data.firstName.trim(),
      lastName: data.lastName.trim(),
      phoneNumber: data.phoneNumber.trim(),
    };

    if (currentProfile?.id) {
      const response = await customersProfilePartialUpdate(
        currentProfile.id,
        payload,
      );
      return response.data;
    }

    const response = await customersProfileCreate(payload as Profile);
    return response.data;
  },
};
