import { requestJson } from "../../shared/json-request";

export interface Access {
  can_write: boolean;
  sign_in_available: boolean;
}

export const publicAccess: Access = { can_write: false, sign_in_available: false };
export const getAccess = () => requestJson<Access>("/api/access");
