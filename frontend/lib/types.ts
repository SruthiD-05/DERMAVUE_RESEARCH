export type DataOrigin = 'demo' | 'local' | 'remote'

export type Sex = 'female' | 'male' | 'intersex' | 'prefer-not-to-say' | 'not-recorded'
export type ConsentStatus = 'obtained' | 'pending' | 'declined' | 'not-required'
export type YesNoUnknown = 'yes' | 'no' | 'unknown'
export type LesionSide = 'left' | 'right' | 'midline' | 'not-applicable'
export type LesionChange = 'no-change' | 'size' | 'color' | 'shape' | 'multiple' | 'unknown'
export type Symptom = 'itching' | 'bleeding' | 'pain' | 'none' | 'unknown'

export interface Patient {
  id: string
  reference: string
  age: number
  dateOfBirth?: string
  sex: Sex
  consent: ConsentStatus
  notes?: string
  origin: DataOrigin
  createdAt: string
}

export interface ClinicalHistory {
  personalSkinCancerHistory: YesNoUnknown
  familySkinCancerHistory: YesNoUnknown
  previousLesionEvaluation: YesNoUnknown
  immunosuppression: YesNoUnknown | 'not-recorded'
  medicalHistory?: string
  medications?: string
  allergies?: string
  notes?: string
}

export interface LesionDetails {
  lesionId: string
  bodyRegion: string
  anatomicalSite?: string
  side: LesionSide
  duration?: string
  change: LesionChange
  symptoms: Symptom[]
  previousTreatment?: string
  observations?: string
  notes?: string
}

export type ImageKind = 'clinical' | 'dermoscopic' | 'additional'

export interface CaseImage {
  id: string
  caseId: string
  kind: ImageKind
  label?: string
  filename: string
  mimeType: string
  sizeBytes: number
  width?: number
  height?: number
  /** Data URL for locally stored images, or a public path for bundled demo assets. */
  src: string
  uploadedAt: string
}

export type CaseStatus =
  | 'draft'
  | 'ready'
  | 'pending'
  | 'complete'
  | 'unavailable'

export type ReviewStatus = 'unreviewed' | 'in-review' | 'reviewed'

export interface ClassScore {
  label: string
  score: number
}

export interface AnalysisResult {
  id: string
  caseId: string
  /** 'demo' results are synthetic UI demonstrations and never produced by a model. */
  source: 'demo' | 'model'
  predictedLabel: string
  scores?: ClassScore[]
  scoresAreCalibrated?: boolean
  scoreSource?: 'cnn_auxiliary' | 'final_fused' | 'unknown'
  scoreSemantics?: string
  diagnosisLevel?: 'binary' | 'multiclass' | 'unknown'
  subtypeAvailable?: boolean
  subtypeUnavailableReason?: string
  modelName?: string
  modelVersion?: string
  inputImageId?: string
  inferredAt: string
  explanationAvailable: boolean
  riskLevel?: 'LOW' | 'MODERATE' | 'HIGH'
  screeningFlag?: boolean
  malignancyScore?: number
  numImages?: number
  inputMetadata?: {
    ageProvided?: boolean
    sexProvided?: boolean
    localizationProvided?: boolean
  }
  streamScores?: Record<string, number>
  disclaimer?: string
}

export interface CaseNote {
  id: string
  body: string
  createdAt: string
}

export interface Case {
  id: string
  /** Internal stable storage/API identifier; never replaced by user labels. */
  caseReference?: string
  caseName?: string
  patientId: string
  status: CaseStatus
  reviewStatus: ReviewStatus
  history: ClinicalHistory
  lesion: LesionDetails
  imageIds: string[]
  result?: AnalysisResult
  notes: CaseNote[]
  followUp?: string
  origin: DataOrigin
  createdAt: string
  updatedAt: string
}

export type ModelConnectionState =
  | 'connected'
  | 'disconnected'
  | 'checkpoint-missing'
  | 'artifacts-invalid'
  | 'artifacts-present'
  | 'release-disabled'
  | 'release-approved'
  | 'research-enabled-not-loaded'
  | 'research-available'
  | 'inference-unavailable'
  | 'configuration-required'
  | 'loading'

export interface ModelStatus {
  state: ModelConnectionState
  backendConfigured: boolean
  modelName?: string
  modelVersion?: string
  checkpointLoaded?: boolean
  inferenceAvailable: boolean
  architecture?: string
  artifactState?: string
  loadState?: string
  releaseState?: string
  metadataSource?: string
  reportedMetrics?: Record<string, { value?: number; label?: string }>
  researchMode?: boolean
  lastCheckedAt?: string
  message: string
}

export interface ModelInfo {
  name?: string
  version?: string
  architecture?: string
  supportedInputs?: ImageKind[]
  allowedLocalizations?: string[]
  sexValues?: string[]
  outputCategories?: string[]
  returnsProbabilities?: boolean
  diagnosisLevel?: 'binary' | 'multiclass' | 'unknown'
  subtypeAvailable?: boolean
  auxiliaryOutputCategories?: string[]
  returnsAuxiliaryClassScores?: boolean
  scoreSemantics?: string
  developerReportedAccuracy?: string
  metadataSource?: string
  reportedMetrics?: Record<string, { value?: number; label?: string }>
  verification?: {
    artifactHashesVerified?: boolean
    evaluationGatePassed?: boolean
    servingEnabled?: boolean
  }
  evaluation?: {
    dataset?: string
    sampleSize?: number
    splitMethodology?: string
    metrics?: Record<string, string>
    evaluatedAt?: string
    limitations?: string[]
  }
}

export interface CaseWithPatient extends Case {
  patient?: Patient
  images: CaseImage[]
}

export interface WorkspaceSettings {
  workspaceName: string
  displayName: string
  showDemoData: boolean
  maxUploadMb: number
}
