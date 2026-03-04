export type CountryCode = string; // "PL" | "DE" | "US" itd.

export type CountryField = {
  code: CountryCode;
  name: string;
};

export interface Address {
  id: string;
  street: string;
  street2?: string;
  city: string;
  state?: string;
  postal_code: string;
  country: CountryField;
  is_default: boolean;
}
