pipeline {
    agent any 

    stages {
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