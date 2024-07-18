pipeline {
    agent any

    stages {
        stage('Start') {
            echo 'Start'
        }

        stage('Run') {
            steps {
                sh 'python3 importstack.py'
            }
        }

        stage ('Complete') {
            steps {
                echo 'Completed'
            }
        }
    }
}