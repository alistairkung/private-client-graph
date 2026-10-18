import { requestJson } from "../../shared/json-request";

export interface Access {
  can_write: boolean;
  sign_in_available: boolean;
}

export const getAccess = () => requestJson<Access>("/api/access");
