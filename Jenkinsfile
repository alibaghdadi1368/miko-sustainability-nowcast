// CI pipeline for Miko. Jenkins runs this file for every branch and every new commit.
pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 40, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    environment {
        // One conda env per branch, outside the workspace: it survives cleanWs() and is
        // reused by the next build. Delete the folder if environment.yml changes.
        CONDA_ENV = "/var/jenkins_home/conda-envs/miko-${env.BRANCH_NAME.replace('/', '-')}"
        PYTHONUNBUFFERED = '1'
    }

    stages {
        stage('Setup') {
            steps {
                sh '''
                    conda --version
                    if [ ! -d "$CONDA_ENV" ]; then
                        conda env create --prefix "$CONDA_ENV" --file environment.yml
                    fi
                    conda run --prefix "$CONDA_ENV" python -m pip install -e ".[dev]"
                    conda run --no-capture-output --prefix "$CONDA_ENV" java -version
                '''
            }
        }
        stage('Lint') {
            steps {
                sh 'conda run --no-capture-output --prefix "$CONDA_ENV" make lint'
            }
        }
        stage('Unit tests') {
            steps {
                sh 'conda run --no-capture-output --prefix "$CONDA_ENV" pytest -m "not spark" --junitxml=reports/unit.xml'
            }
        }
        stage('Spark tests') {
            steps {
                sh 'conda run --no-capture-output --prefix "$CONDA_ENV" pytest -m spark --junitxml=reports/spark.xml'
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'reports/*.xml'
        }
        cleanup {
            cleanWs()
        }
    }
}
