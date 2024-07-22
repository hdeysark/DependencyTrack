pipeline {
    agent any

    parameters {
        string(name: 'stackName', defaultValue: '', description: 'Enter the Stack Name')
        string(name: 'buildNumber', defaultValue: '', description: 'Enter the Build Number')
    }

    environment {
        API_KEY = credentials('depTrack_local_API_KEY')
        BASE_URL = credentials('depTrack_local_baseurl')
        STACK_NAME = "${params.stackName}"
        BUILD_NUMBER = "${params.buildNumber}"
    }

    stages {
        stage('Start') {
            steps{
                echo 'Start'
            }
        }

        stage('Run') {
            steps {
                sh '''
                    export STACK_NAME=${STACK_NAME}
                    export BUILD_NUMBER=${BUILD_NUMBER}
                    python3 importstack.py
                '''
            }
        }

        stage ('Complete') {
            steps {
                echo 'Completed'
            }
        }
    }
}