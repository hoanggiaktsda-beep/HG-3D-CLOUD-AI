/** Honest disconnected boundary. No network, storage or pretend job results. */
export class BackendUnavailableError extends Error {
  constructor() { super('CHƯA KẾT NỐI backend, AI thị giác và worker Blender.'); this.name = 'BackendUnavailableError'; }
}
export class ModelService {
  capabilities() {
    return Object.freeze({ connected: false, vision: false, blender: false, privateStorage: false, authenticated: false });
  }
  async createJob() { throw new BackendUnavailableError(); }
  async getJob() { throw new BackendUnavailableError(); }
  async requestRevision() { throw new BackendUnavailableError(); }
  async getArtifacts() { throw new BackendUnavailableError(); }
}
export const modelService = new ModelService();
