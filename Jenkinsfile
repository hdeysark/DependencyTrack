pipeline {
    agent any

    stages {
        stage('Start') {
            steps{
                echo 'Start'
            }
        }

        stage('Run') {
            steps {
                sh 'python importstack.py'
            }
        }

        stage ('Complete') {
            steps {
                echo 'Completed'
            }
        }
    }
}