import React, { useState } from 'react'
import {
  api,
  DecisionCase,
  FormalizeResponse,
  JobResult,
} from './api'
import { AppHeader } from './components/AppHeader'
import { LandingPage } from './components/LandingPage'
import { CaseWorkspace } from './components/CaseWorkspace'
import { ModelApprovalGate } from './components/ModelApprovalGate'
import { RecommendationView } from './components/RecommendationView'
import { HelpCenterModal } from './components/HelpCenterModal'
import { BrainModal } from './components/BrainModal'
import { ApiPortalModal } from './components/ApiPortalModal'

type AppStage = 'INTAKE' | 'CASE_WORKSPACE' | 'MODEL_APPROVAL' | 'RECOMMENDATION'

export const App: React.FC = () => {
  const [stage, setStage] = useState<AppStage>('INTAKE')
  const [isLoading, setIsLoading] = useState(false)
  const [statusMessage, setStatusMessage] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // Modals state
  const [isHelpOpen, setIsHelpOpen] = useState(false)
  const [isBrainOpen, setIsBrainOpen] = useState(false)
  const [isApiPortalOpen, setIsApiPortalOpen] = useState(false)

  // Current session data
  const [sessionId, setSessionId] = useState<string>(() => 'sess_' + Math.random().toString(36).substring(2, 12))
  const [userQuery, setUserQuery] = useState('')
  const [problemClass, setProblemClass] = useState<string>('CHOICE')
  const [intakeExplanation, setIntakeExplanation] = useState<string>('')
  const [decisionCase, setDecisionCase] = useState<DecisionCase | null>(null)
  const [formalized, setFormalized] = useState<FormalizeResponse | null>(null)
  const [primaryResult, setPrimaryResult] = useState<JobResult | null>(null)
  const [comparisonResult, setComparisonResult] = useState<JobResult | null>(null)

  const handleReset = () => {
    setStage('INTAKE')
    setSessionId('sess_' + Math.random().toString(36).substring(2, 12))
    setUserQuery('')
    setProblemClass('CHOICE')
    setIntakeExplanation('')
    setDecisionCase(null)
    setFormalized(null)
    setPrimaryResult(null)
    setComparisonResult(null)
    setErrorMessage(null)
    setStatusMessage(null)
  }

  // 1. Analyze case from user intake text (E1: Single Intake Pathway via /cognitive/intake)
  const handleIntakeSubmit = async (text: string, problemClassOverride?: string) => {
    setIsLoading(true)
    setErrorMessage(null)
    setUserQuery(text)
    setStatusMessage('Percepcja kognitywna i formalizacja zadania (Active Inference)...')

    try {
      const intakeRes = await api.cognitiveIntake({
        query: text,
        session_id: sessionId,
        problem_class_override: problemClassOverride,
      })

      if (intakeRes.session_id) {
        setSessionId(intakeRes.session_id)
      }

      if (intakeRes.explanation) {
        setIntakeExplanation(intakeRes.explanation)
      }

      if (intakeRes.status === 'not_computable') {
        const reason = intakeRes.not_computable_report?.reason ||
          'Zadanie nie ma charakteru obliczeniowego (kwestia etyczna, światopoglądowa lub emocjonalna).'
        const suggested = intakeRes.not_computable_report?.reframe_suggestions?.join(' ') ||
          'Zalecana dyskusja ludzka lub zdefiniowanie mierzalnych wskaźników zastępczych.'
        setErrorMessage(`[Brak możliwości obliczeniowej] ${reason} ${suggested}`)
        return
      }

      if (intakeRes.status === 'needs_clarification' && !intakeRes.decision_case) {
        const reason = intakeRes.explanation || 'Opis wymaga zdefiniowania wariantów decyzyjnych.'
        const suggestions = intakeRes.questions?.length
          ? ` Sugestia: ${intakeRes.questions.join(' ')}`
          : ' Zdefiniuj co najmniej dwie opcje do wyboru (np. "Wybierz między opcją A a B").'
        setErrorMessage(`[Wymaga uściślenia] ${reason}${suggestions}`)
        return
      }

      if (intakeRes.problem_class) {
        setProblemClass(intakeRes.problem_class)
      }

      if (intakeRes.decision_case) {
        setDecisionCase(intakeRes.decision_case)
      }
      if (intakeRes.formalized) {
        setFormalized(intakeRes.formalized)
      }

      if (intakeRes.decision_case) {
        setStage('CASE_WORKSPACE')
      } else {
        setErrorMessage(intakeRes.explanation || 'Nie udało się wyodrębnić wariantów decyzyjnych. Podaj co najmniej dwie opcje do porównania.')
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Wystąpił błąd podczas analizy kognitywnej'
      setErrorMessage(msg)
    } finally {
      setIsLoading(false)
      setStatusMessage(null)
    }
  }

  // 2. Answer an unknown in CaseWorkspace
  const handleAnswerUnknown = (unknownId: string, answer: string) => {
    if (!decisionCase) return
    const updatedUnknowns = decisionCase.unknowns.map((u) =>
      u.id === unknownId ? { ...u, answer, is_resolved: true } : u
    )
    const updatedCase = { ...decisionCase, unknowns: updatedUnknowns }
    setDecisionCase(updatedCase)
  }

  // 3. Move from CaseWorkspace to ModelApprovalGate
  const handleProceedToModeling = async () => {
    if (decisionCase) {
      setIsLoading(true)
      setStatusMessage('Przygotowywanie modelu na podstawie Twoich opcji i odpowiedzi...')
      try {
        const formalData = await api.formalizeCase(decisionCase)
        setFormalized(formalData)
      } catch (err: unknown) {
        console.warn('Could not re-formalize case with answers, using base model:', err)
      } finally {
        setIsLoading(false)
        setStatusMessage(null)
      }
    }
    setStage('MODEL_APPROVAL')
  }

  // 4. Approve model and run solver
  const handleApproveAndSolve = async (
    solverChoice: 'cp_sat' | 'qaoa_aer' | 'both',
    editedWeights?: Record<string, number>
  ) => {
    if (!formalized) return
    setIsLoading(true)
    setErrorMessage(null)
    setStatusMessage('Tworzenie i rejestracja modelu zadania...')

    try {
      const objCoeffs = editedWeights || formalized.objective_coefficients
      // 1. Create Problem in backend (starts unapproved)
      const probRes = await api.createProblem({
        description: userQuery || formalized.description_raw,
        binary_variables: formalized.binary_variables,
        objective_coefficients: objCoeffs,
        objective_direction: formalized.objective_direction,
        equality_constraints: formalized.equality_constraints,
        approved: false,
      })

      // 2. Explicitly approve problem (Publication gate requirement)
      setStatusMessage('Zatwierdzanie formalne modelu przed obliczeniami...')
      await api.approveProblem(probRes.problem_id)

      // 3. Submit solver jobs
      if (solverChoice === 'both') {
        setStatusMessage('Uruchamianie solvera klasycznego oraz symulacji kwantowej (Benchmark)...')
        const bench = await api.createBenchmark({ problem_id: probRes.problem_id })

        // Poll both jobs
        const [res1, res2] = await Promise.all([
          pollJobResult(bench.cp_sat_job_id),
          pollJobResult(bench.qaoa_job_id),
        ])

        setPrimaryResult(res1)
        setComparisonResult(res2)
      } else {
        setStatusMessage(`Rozwiązywanie zadania za pomocą silnika ${solverChoice === 'cp_sat' ? 'CP-SAT' : 'QAOA Aer'}...`)
        const job = await api.createJob({
          problem_id: probRes.problem_id,
          solver: solverChoice,
          metadata: sessionId ? { session_id: sessionId } : undefined,
        })

        const res = await pollJobResult(job.job_id)
        setPrimaryResult(res)
        setComparisonResult(null)
      }

      setStage('RECOMMENDATION')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Wystąpił błąd podczas rozwiązywania zadania'
      setErrorMessage(msg)
    } finally {
      setIsLoading(false)
      setStatusMessage(null)
    }
  }

  // Polling helper
  const pollJobResult = async (jobId: string): Promise<JobResult> => {
    const maxAttempts = 40
    for (let i = 0; i < maxAttempts; i++) {
      const status = await api.getJobStatus(jobId)
      if (['COMPLETED', 'FAILED', 'TIMED_OUT', 'CANCELLED'].includes(status.execution_status)) {
        return api.getJobResult(jobId)
      }
      await new Promise((r) => setTimeout(r, 600))
    }
    throw new Error('Przekroczono limit czasu oczekiwania na wynik obliczeń.')
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      background: stage === 'INTAKE' ? 'oklch(6% 0.01 250)' : 'var(--bg-canvas)',
      color: stage === 'INTAKE' ? 'oklch(96% 0.01 250)' : 'var(--text-primary)',
    }}>
      {/* AppHeader only shown after INTAKE — LandingPage manages its own nav */}
      {stage !== 'INTAKE' && (
        <AppHeader
          onReset={handleReset}
          isBusy={isLoading}
          onOpenHelp={() => setIsHelpOpen(true)}
          onOpenBrain={() => setIsBrainOpen(true)}
          onOpenApiPortal={() => setIsApiPortalOpen(true)}
        />
      )}

      {/* Global notifications */}
      {statusMessage && (
        <div style={{
          background: 'var(--status-unverified-bg)',
          borderBottom: '1px solid var(--status-unverified-border)',
          padding: '0.75rem 2rem',
          fontSize: '0.875rem',
          color: 'var(--status-unverified-text)',
          textAlign: 'center',
          fontWeight: 600,
          position: 'sticky',
          top: 0,
          zIndex: 1000,
        }}>
          {statusMessage}
        </div>
      )}

      {errorMessage && (
        <div style={{
          background: 'var(--status-rejected-bg)',
          borderBottom: '1px solid var(--status-rejected-border)',
          padding: '0.875rem 2rem',
          fontSize: '0.9375rem',
          color: 'var(--status-rejected-text)',
          textAlign: 'center',
          fontWeight: 600,
          position: 'sticky',
          top: 0,
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1rem',
        }}>
          <span>{errorMessage}</span>
          <button
            onClick={() => setErrorMessage(null)}
            type="button"
            style={{
              background: 'transparent',
              border: '1px solid currentColor',
              color: 'inherit',
              borderRadius: '4px',
              padding: '0.2rem 0.6rem',
              cursor: 'pointer',
              fontSize: '0.75rem',
              fontWeight: 700,
            }}
          >
            Zamknij ✕
          </button>
        </div>
      )}

      {/* Main content stage */}
      <main style={{ flex: 1, paddingBottom: stage === 'INTAKE' ? 0 : '3rem' }}>
        {stage === 'INTAKE' && (
          <LandingPage
            onSubmit={handleIntakeSubmit}
            isLoading={isLoading}
            errorMessage={errorMessage}
            onClearError={() => setErrorMessage(null)}
            initialText={userQuery}
            onOpenHelp={() => setIsHelpOpen(true)}
            onOpenBrain={() => setIsBrainOpen(true)}
            onOpenApiPortal={() => setIsApiPortalOpen(true)}
          />
        )}

        {stage === 'CASE_WORKSPACE' && (
          decisionCase ? (
            <CaseWorkspace
              decisionCase={decisionCase}
              problemClass={problemClass}
              problemClassReason={intakeExplanation || undefined}
              onOverrideProblemClass={(newClass) => {
                setProblemClass(newClass)
                if (userQuery) {
                  handleIntakeSubmit(userQuery, newClass)
                }
              }}
              onAnswerUnknown={handleAnswerUnknown}
              onUpdateCase={setDecisionCase}
              onProceedToModeling={handleProceedToModeling}
              onBackToEdit={() => setStage('INTAKE')}
              isLoading={isLoading}
            />
          ) : (
            <div style={{ textAlign: 'center', padding: '5rem 2rem' }}>
              <p style={{ fontSize: '1.125rem', color: 'var(--text-muted)' }}>
                Brak aktywnego przypadku decyzyjnego do wyświetlenia.
              </p>
              <button
                type="button"
                onClick={handleReset}
                className="btn-primary"
                style={{ marginTop: '1.5rem', padding: '0.75rem 1.5rem', cursor: 'pointer' }}
              >
                ← Wróć do strony głównej
              </button>
            </div>
          )
        )}

        {stage === 'MODEL_APPROVAL' && formalized && (
          <ModelApprovalGate
            formalized={formalized}
            decisionCase={decisionCase}
            onApproveAndSolve={handleApproveAndSolve}
            onBack={() => setStage('CASE_WORKSPACE')}
            isSolving={isLoading}
          />
        )}

        {stage === 'RECOMMENDATION' && primaryResult && (
          <RecommendationView
            decisionCase={decisionCase}
            result={primaryResult}
            comparisonResult={comparisonResult}
            onStartNew={handleReset}
            breakEvenPoint={formalized?.break_even_point || decisionCase?.break_even_point}
            sessionId={sessionId}
            problemClass={problemClass}
          />
        )}
      </main>

      {/* Modals */}
      <HelpCenterModal
        isOpen={isHelpOpen}
        onClose={() => setIsHelpOpen(false)}
        currentStage={stage}
        onSelectExample={handleIntakeSubmit}
      />

      <BrainModal
        isOpen={isBrainOpen}
        onClose={() => setIsBrainOpen(false)}
        onGoToDilemma={() => {
          setIsBrainOpen(false)
          window.scrollTo({ top: 0, behavior: 'smooth' })
        }}
      />

      <ApiPortalModal
        isOpen={isApiPortalOpen}
        onClose={() => setIsApiPortalOpen(false)}
      />

      {/* Footer only shown after INTAKE stages */}
      {stage !== 'INTAKE' && (
        <footer
          className="no-print"
          style={{
            textAlign: 'center',
            padding: '1.5rem',
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          borderTop: '1px solid var(--border-subtle)',
          background: 'var(--bg-surface)',
        }}>
          YourQuantum · Ścisłe obliczenia i niezależna weryfikacja dla codziennych wyborów
        </footer>
      )}
    </div>
  )
}

export default App

