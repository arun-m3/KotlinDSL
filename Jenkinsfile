pipeline {
    agent any

    parameters {
        choice(
            name: 'TEAMCITY_VERSION',
            choices: ['2025.07'],
            description: 'TeamCity version to test against'
        )
        choice(
            name: 'TEST_SUITE',
            choices: ['all', 'import', 'sync', 'pipeline'],
            description: 'Test suite to execute'
        )
        booleanParam(
            name: 'CLEANUP_AFTER_TESTS',
            defaultValue: true,
            description: 'Clean up test resources after execution'
        )
    }

    environment {
        PYTHON_VERSION = '3.11'
        TEAMCITY_URL = 'http://localhost:8111'
        TEAMCITY_USERNAME = 'admin'
        TEAMCITY_PASSWORD = 'admin'
    }

    stages {
        stage('Setup Environment') {
            steps {
                script {
                    echo "Setting up TeamCity DSL test environment"
                    sh '''
                        python -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                    '''
                }
            }
        }

        stage('Start TeamCity') {
            steps {
                script {
                    sh '''
                        echo "Starting TeamCity version ${TEAMCITY_VERSION}"
                        docker-compose down -v || true
                        TEAMCITY_VERSION=${TEAMCITY_VERSION} docker-compose up -d

                        # Wait for TeamCity to be ready
                        timeout 600 bash -c 'until curl -f http://localhost:8111/app/rest/server 2>/dev/null; do sleep 10; done'
                        echo "TeamCity is ready"
                    '''
                }
            }
        }

        stage('Run Tests') {
            parallel {
                stage('DSL Import Tests') {
                    when {
                        anyOf {
                            params.TEST_SUITE == 'all'
                            params.TEST_SUITE == 'import'
                        }
                    }
                    steps {
                        script {
                            sh '''
                                . venv/bin/activate
                                pytest tests/test_dsl_import.py -v \
                                    --html=reports/import-report.html \
                                    --json-report --json-report-file=reports/import-report.json \
                                    --tb=short
                            '''
                        }
                    }
                }

                stage('Synchronization Tests') {
                    when {
                        anyOf {
                            params.TEST_SUITE == 'all'
                            params.TEST_SUITE == 'sync'
                        }
                    }
                    steps {
                        script {
                            sh '''
                                . venv/bin/activate
                                pytest tests/test_synchronization.py -v \
                                    --html=reports/sync-report.html \
                                    --json-report --json-report-file=reports/sync-report.json \
                                    --tb=short
                            '''
                        }
                    }
                }

                stage('Pipeline Execution Tests') {
                    when {
                        anyOf {
                            params.TEST_SUITE == 'all'
                            params.TEST_SUITE == 'pipeline'
                        }
                    }
                    steps {
                        script {
                            sh '''
                                . venv/bin/activate
                                pytest tests/test_pipeline_execution.py -v \
                                    --html=reports/pipeline-report.html \
                                    --json-report --json-report-file=reports/pipeline-report.json \
                                    --tb=short
                            '''
                        }
                    }
                }
            }
        }

        stage('Generate Report') {
            steps {
                script {
                    sh '''
                        . venv/bin/activate
                        python scripts/generate_comprehensive_report.py \
                            --artifacts-dir reports/ \
                            --output reports/comprehensive-report.html \
                            --format html
                    '''
                }
            }
        }
    }

    post {
        always {
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'reports',
                reportFiles: 'comprehensive-report.html',
                reportName: 'TeamCity DSL Test Report'
            ])

            archiveArtifacts artifacts: 'reports/**/*', fingerprint: true

            script {
                if (params.CLEANUP_AFTER_TESTS) {
                    sh '''
                        python scripts/cleanup.py || true
                        docker-compose down -v || true
                    '''
                }
            }
        }

        success {
            echo 'TeamCity DSL tests completed successfully!'
        }

        failure {
            echo 'TeamCity DSL tests failed. Check the reports for details.'
        }
    }
}