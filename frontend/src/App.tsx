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

type AppStage = 'INTAKE' | 'CASE_WORKSPACE' | 'MODEL_APPROVAL' | 'RECOMMENDATION'

export const App: React.FC = () => {
  const [stage, setStage] = useState<AppStage>('INTAKE')
  const [isLoading, setIsLoading] = useState(false)
  const [statusMessage, setStatusMessage] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // Modals state
  const [isHelpOpen, setIsHelpOpen] = useState(false)
  const [isBrainOpen, setIsBrainOpen] = useState(false)

  // Current session data
  const [userQuery, setUserQuery] = useState('')
  const [decisionCase, setDecisionCase] = useState<DecisionCase | null>(null)
  const [formalized, setFormalized] = useState<FormalizeResponse | null>(null)
  const [primaryResult, setPrimaryResult] = useState<JobResult | null>(null)
  const [comparisonResult, setComparisonResult] = useState<JobResult | null>(null)

  const handleReset = () => {
    setStage('INTAKE')
    setUserQuery('')
    setDecisionCase(null)
    setFormalized(null)
    setPrimaryResult(null)
    setComparisonResult(null)
    setErrorMessage(null)
    setStatusMessage(null)
  }

  // 1. Analyze case from user intake text
  const handleIntakeSubmit = async (text: string) => {
    setIsLoading(true)
    setErrorMessage(null)
    setUserQuery(text)
    setStatusMessage('Analizowanie sytuacji i mapowanie wariantów...')

    try {
      // Parallel: analyze human case and formalize mathematical rules
      const [caseData, formalData] = await Promise.all([
        api.analyzeCase(text),
        api.formalizeProblem(text),
      ])

      setDecisionCase(caseData)
      setFormalized(formalData)
      setStage('CASE_WORKSPACE')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Wystąpił błąd podczas analizy'
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
  const handleApproveAndSolve = async (solverChoice: 'cp_sat' | 'qaoa_aer' | 'both') => {
    if (!formalized) return
    setIsLoading(true)
    setErrorMessage(null)
    setStatusMessage('Tworzenie i rejestracja modelu zadania...')

    try {
      // 1. Create Problem in backend (starts unapproved)
      const probRes = await api.createProblem({
        description: userQuery || formalized.description_raw,
        binary_variables: formalized.binary_variables,
        objective_coefficients: formalized.objective_coefficients,
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
        />
      )}

      {/* Global notifications (non-INTAKE stages only) */}
      {stage !== 'INTAKE' && statusMessage && (
        <div style={{
          background: 'var(--status-unverified-bg)',
          borderBottom: '1px solid var(--status-unverified-border)',
          padding: '0.75rem 2rem',
          fontSize: '0.875rem',
          color: 'var(--status-unverified-text)',
          textAlign: 'center',
          fontWeight: 500,
        }}>
          {statusMessage}
        </div>
      )}

      {stage !== 'INTAKE' && errorMessage && (
        <div style={{
          background: 'var(--status-rejected-bg)',
          borderBottom: '1px solid var(--status-rejected-border)',
          padding: '0.75rem 2rem',
          fontSize: '0.875rem',
          color: 'var(--status-rejected-text)',
          textAlign: 'center',
          fontWeight: 500,
        }}>
          {errorMessage}
        </div>
      )}

      {/* Main content stage */}
      <main style={{ flex: 1, paddingBottom: stage === 'INTAKE' ? 0 : '3rem' }}>
        {stage === 'INTAKE' && (
          <LandingPage
            onSubmit={handleIntakeSubmit}
            isLoading={isLoading}
            onOpenHelp={() => setIsHelpOpen(true)}
            onOpenBrain={() => setIsBrainOpen(true)}
          />
        )}

        {stage === 'CASE_WORKSPACE' && decisionCase && (
          <CaseWorkspace
            decisionCase={decisionCase}
            onAnswerUnknown={handleAnswerUnknown}
            onUpdateCase={setDecisionCase}
            onProceedToModeling={handleProceedToModeling}
            onBackToEdit={() => setStage('INTAKE')}
            isLoading={isLoading}
          />
        )}

        {stage === 'MODEL_APPROVAL' && formalized && (
          <ModelApprovalGate
            formalized={formalized}
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

