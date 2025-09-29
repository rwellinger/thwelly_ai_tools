export interface UserSettings {
  songListLimit: number;
  imageListLimit: number;
}

export const DEFAULT_USER_SETTINGS: UserSettings = {
  songListLimit: 10,
  imageListLimit: 10
};