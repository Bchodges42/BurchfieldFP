document.querySelector('#btnShowAnimals').addEventListener('click', function(){
    document.querySelector('#card1').classList.remove('d-none')
    document.querySelector('#card2').classList.add('d-none')
    document.querySelector('#card3').classList.add('d-none')
})

document.querySelector('#btnShowFeeding').addEventListener('click', function(){
    document.querySelector('#card1').classList.add('d-none')
    document.querySelector('#card2').classList.remove('d-none')
    document.querySelector('#card3').classList.add('d-none')
})

document.querySelector('#btnShowVetVisits').addEventListener('click', function(){
    document.querySelector('#card1').classList.add('d-none')
    document.querySelector('#card2').classList.add('d-none')
    document.querySelector('#card3').classList.remove('d-none')
})

document.querySelector('#btnSaveAnimal').addEventListener('click', function(){
    let strAnimalType = document.querySelector('#txtAnimalType').value.trim()
    let strBreed = document.querySelector('#txtBreed').value.trim()
    let strDOB = document.querySelector('#txtDOB').value.trim()
    let strSire = document.querySelector('#txtSire').value.trim()
    let strDam = document.querySelector('#txtDam').value.trim()
    let strBirthWeight = document.querySelector('#txtBirthWeight').value.trim()
    let strAnimalID = document.querySelector('#txtAnimalID').value.trim()
    let strDescription = document.querySelector('#txtDescription').value.trim()
    let strLocation = document.querySelector('#txtLocation').value.trim()
    let strAnimalNotes = document.querySelector('#txtAnimalNotes').value.trim()

    let blnError = false
    let strError = ''

    if(strAnimalType == ''){
        blnError = true
        strError += '<p>You must enter an animal type</p>'
    }
    if(strBreed == ''){
        blnError = true
        strError += '<p>You must enter a breed</p>'
    }
    if(strDOB == ''){
        blnError = true
        strError += '<p>You must enter a date of birth</p>'
    }
    if(strBirthWeight == ''){
        blnError = true
        strError += '<p>You must enter birth weight</p>'
    }
    if(strAnimalID == ''){
        blnError = true
        strError += '<p>You must enter an animal ID</p>'
    }
    if(strDescription == ''){
        blnError = true
        strError += '<p>You must enter a description</p>'
    }
    if(strLocation == ''){
        blnError = true
        strError += '<p>You must enter a location</p>'
    }

    if(blnError == true){
        Swal.fire({
            title: 'You are missing required info:',
            html: strError,
            icon: 'warning',
            confirmButtonColor: '#b60f0fff',
        })
    } else if(blnError == false){
        fetch('http://localhost:8000/animals', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                animaltype: strAnimalType,
                breed: strBreed,
                dob: strDOB,
                sire: strSire,
                dam: strDam,
                birthweight: strBirthWeight,
                animalid: strAnimalID,
                description: strDescription,
                location: strLocation,
                notes: strAnimalNotes
            })
        })
        .then(response => response.json())
        .then(data => {
            Swal.fire({
                title: 'Animal Saved Successfully!',
                icon: 'success',
                confirmButtonColor: '#189b23a9',
            })
            document.querySelector('#formAnimal').reset()
        })
    }
})

document.querySelector('#btnSaveFeeding').addEventListener('click', function(){
    let strAnimalID = document.querySelector('#txtFeedingAnimalID').value.trim()
    let strTimeOfDay = document.querySelector('#txtTimeOfDay').value.trim()
    let strHowMuch = document.querySelector('#txtHowMuch').value.trim()
    let strWhatFeeding = document.querySelector('#txtWhatFeeding').value.trim()

    let blnError = false
    let strError = ''

    if(strAnimalID == ''){
        blnError = true
        strError += '<p>You must select an animal</p>'
    }
    if(strTimeOfDay == ''){
        blnError = true
        strError += '<p>You must enter a time of day</p>'
    }
    if(strHowMuch == ''){
        blnError = true
        strError += '<p>You must enter how much to feed</p>'
    }
    if(strWhatFeeding == ''){
        blnError = true
        strError += '<p>You must enter what you are feeding</p>'
    }

    if(blnError == true){
        Swal.fire({
            title: 'You are missing required info:',
            html: strError,
            icon: 'warning',
            confirmButtonColor: '#b60f0fff',
        })
    } else if(blnError == false){
        fetch('http://localhost:8000/feeding', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
             body: JSON.stringify({
                animalid: strAnimalID,
                timeofday: strTimeOfDay,
                howmuch: strHowMuch,
                whatfeeding: strWhatFeeding
            })
        })
        .then(response => response.json())
        .then(data => {
            Swal.fire({
                title: 'Feeding Schedule Saved Successfully!',
                icon: 'success',
                confirmButtonColor: '#189b23a9',
            })
            document.querySelector('#formFeeding').reset()
        })
    }
})

document.querySelector('#btnSaveVetVisit').addEventListener('click', function(){
    let strAnimalID = document.querySelector('#txtVetAnimalID').value.trim()
    let strVisitDate = document.querySelector('#txtVisitDate').value.trim()
    let strVisitReason = document.querySelector('#selVisitReason').value.trim()
    let strInoculations = document.querySelector('#txtInoculations').value.trim()
    let strSizeAtVisit = document.querySelector('#txtSizeAtVisit').value.trim()
    let strVetName = document.querySelector('#txtVetName').value.trim()
    let strVetNotes = document.querySelector('#txtVetNotes').value.trim()

    let blnError = false
    let strError = ''

    if(strAnimalID == ''){
        blnError = true
        strError += '<p>You must select an animal</p>'
    }
    if(strVisitDate == ''){
        blnError = true
        strError += '<p>You must enter a visit date</p>'
    }
    if(strVisitReason == ''){
        blnError = true
        strError += '<p>You must select a visit reason</p>'
    }
    if(strInoculations == ''){
        blnError = true
        strError += '<p>You must enter inoculations</p>'
    }
    if(strSizeAtVisit == ''){
        blnError = true
        strError += '<p>You must enter size at visit</p>'
    }
    if(strVetName == ''){
        blnError = true
        strError += '<p>You must enter veterinary name</p>'
    }

    if(blnError == true){
        Swal.fire({
            title: 'You are missing required info:',
            html: strError,
            icon: 'warning',
            confirmButtonColor: '#b60f0fff',
        })
    } else if(blnError == false){
        fetch('http://localhost:8000/vetvisits', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                animalid: strAnimalID,
                visitdate: strVisitDate,
                reason: strVisitReason,
                inoculations: strInoculations,
                sizeatvisit: strSizeAtVisit,
                vetname: strVetName,
                notes: strVetNotes
            })
        })
        .then(response => response.json())
        .then(data => {
            Swal.fire({
                title: 'Vet Visit Saved Successfully!',
                icon: 'success',
                confirmButtonColor: '#189b23a9',
            })
            document.querySelector('#formVetVisit').reset()
        })
    }
})