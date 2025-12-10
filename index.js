const express = require('express');
const sqlite3 = require('sqlite3').verbose()
const {v4: uuidv4} = require('uuid')
const HTTP_PORT = 8000
const dbSource = "livestock.db"
const db = new sqlite3.Database(dbSource)

db.serialize(() => {
    db.run(`CREATE TABLE IF NOT EXISTS tblAnimals (
        AnimalID TEXT PRIMARY KEY,
        AnimalType TEXT,
        Breed TEXT,
        DOB TEXT,
        Sire TEXT,
        Dam TEXT,
        BirthWeight TEXT,
        Description TEXT,
        Location TEXT,
        Notes TEXT
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS tblFeedingSchedules (
        FeedingID TEXT PRIMARY KEY,
        AnimalID TEXT,
        TimeOfDay TEXT,
        HowMuch TEXT,
        WhatFeeding TEXT
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS tblVetVisits (
        VetVisitID TEXT PRIMARY KEY,
        AnimalID TEXT,
        VisitDate TEXT,
        Reason TEXT,
        Inoculations TEXT,
        SizeAtVisit TEXT,
        VetName TEXT,
        Notes TEXT
    )`);
});

const app = express()
app.use(express.json())
app.use(express.static(__dirname))

app.listen(HTTP_PORT, () => {
    console.log('Server Running on port', HTTP_PORT)
})

// Animals Routes
app.get('/animals', (req, res, next) => {
    let strAnimalID = req.query.animalid
    let strQuery = 'SELECT * FROM tblAnimals WHERE AnimalID = ?'
    db.all(strQuery, [strAnimalID], (err, results) => {
        if(err){
            res.status(401).json({
                error: err 
            })
        } else { 
            res.status(200).json(results)
        }
    })
})

app.post('/animals', (req, res, next) => {
    let strAnimalType = req.body.animaltype
    let strBreed = req.body.breed
    let strDOB = req.body.dob
    let strSire = req.body.sire
    let strDam = req.body.dam
    let strBirthWeight = req.body.birthweight
    let strAnimalID = req.body.animalid
    let strDescription = req.body.description
    let strLocation = req.body.location
    let strNotes = req.body.notes
    let strQuery = 'INSERT INTO tblAnimals (AnimalID, AnimalType, Breed, DOB, Sire, Dam, BirthWeight, Description, Location, Notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    db.all(strQuery, [strAnimalID, strAnimalType, strBreed, strDOB, strSire, strDam, strBirthWeight, strDescription, strLocation, strNotes], (err) => {
        if(err){
            res.status(401).json({
                error: err 
            })
        } else {
            res.status(201).json({
                message: 'Success!'
            })
        }
    })
})

app.put('/animals', (req, res, next) => {
    let strAnimalID = req.body.animalid
    let strLocation = req.body.location
    let strNotes = req.body.notes
    let strQuery = 'UPDATE tblAnimals SET Location = ?, Notes = ? WHERE AnimalID = ?'
    db.all(strQuery, [strLocation, strNotes, strAnimalID], (err) => {
        if(err){
            res.status(401).json({
                error: err 
            })
        } else {
            res.status(201).json({
                message: 'Success!'
            })
        }
    })
})

app.delete('/animals', (req, res, next) => {
    let strAnimalID = req.body.animalid
    let strQuery = 'DELETE FROM tblAnimals WHERE AnimalID = ?'
    db.all(strQuery, [strAnimalID], (err) => {
        if(err){
            res.status(404).json({
                error: err
            })
        } else {
            res.status(200).json({
                message: 'Success!'
            }) 
        }
    })
})

// Feeding
app.get('/feeding', (req, res, next) => {
    let strAnimalID = req.query.animalid
    let strQuery = 'SELECT * FROM tblFeedingSchedules WHERE AnimalID = ?'
    db.all(strQuery, [strAnimalID], (err, results) => {
        if(err){
            res.status(401).json({
                error: err 
            })
        } else { 
            res.status(200).json(results)
        }
    })
})

app.post('/feeding', (req, res, next) => {
    let strAnimalID = req.body.animalid
    let strTimeOfDay = req.body.timeofday
    let strHowMuch = req.body.howmuch
    let strWhatFeeding = req.body.whatfeeding
    let FeedingID = uuidv4()
    let strQuery = 'INSERT INTO tblFeedingSchedules (FeedingID, AnimalID, TimeOfDay, HowMuch, WhatFeeding) VALUES (?, ?, ?, ?, ?)'
    db.all(strQuery, [FeedingID, strAnimalID, strTimeOfDay, strHowMuch, strWhatFeeding], (err) => {
        if(err){
            res.status(401).json({
                error: err 
            })
        } else {
            res.status(201).json({
                message: 'Success!'
            })
        }
    })
})

app.put('/feeding', (req, res, next) => {
    let strFeedingID = req.body.feedingid 
    let strHowMuch = req.body.howmuch
    let strTimeOfDay = req.body.timeofday 
    let strWhatFeeding = req.body.whatfeeding

    let strQuery = 'UPDATE tblFeedingSchedules SET HowMuch = ?, TimeOfDay = ?, WhatFeeding = ? WHERE FeedingID = ?'
    db.run(strQuery, [strHowMuch, strTimeOfDay, strWhatFeeding, strFeedingID], (err) => {
        if(err){
            res.status(401).json({
                error: err 
            })
        } else {
            res.status(201).json({
                message: 'Success!'
            })
        }
    })
})


app.delete('/feeding', (req, res, next) => {
    let strAnimalID = req.body.animalid
    let strQuery = 'DELETE FROM tblFeedingSchedules WHERE AnimalID = ?'
    db.all(strQuery, [strAnimalID], (err) => {
        if(err){
            res.status(404).json({
                error: err
            })
        } else {
            res.status(200).json({
                message: 'Success!'
            }) 
        }
    })
})

// Vet Visits Routes
app.get('/vetvisits', (req, res, next) => {
    let strAnimalID = req.query.animalid
    let strQuery = 'SELECT * FROM tblVetVisits WHERE AnimalID = ?'
    db.all(strQuery, [strAnimalID], (err, results) => {
        if(err){
            res.status(401).json({
                error: err 
            })
        } else { 
            res.status(200).json(results)
        }
    })
})

app.post('/vetvisits', (req, res, next) => {
    let strAnimalID = req.body.animalid
    let strVisitDate = req.body.visitdate
    let strReason = req.body.reason
    let strInoculations = req.body.inoculations
    let strSizeAtVisit = req.body.sizeatvisit
    let strVetName = req.body.vetname
    let strNotes = req.body.notes
    let VetVisitID = uuidv4()
    let strQuery = 'INSERT INTO tblVetVisits (VetVisitID, AnimalID, VisitDate, Reason, Inoculations, SizeAtVisit, VetName, Notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
    db.all(strQuery, [VetVisitID, strAnimalID, strVisitDate, strReason, strInoculations, strSizeAtVisit, strVetName, strNotes], (err) => {
        if(err){
            res.status(401).json({
                error: err 
            })
        } else {
            res.status(201).json({
                message: 'Success!'
            })
        }
    })
})

app.put('/vetvisits', (req, res, next) => {
    let strAnimalID = req.body.animalid
    let strVisitDate = req.body.visitdate
    let strNotes = req.body.notes
    let strQuery = 'UPDATE tblVetVisits SET Notes = ? WHERE AnimalID = ? AND VisitDate = ?'
    db.all(strQuery, [strNotes, strAnimalID, strVisitDate], (err) => {
        if(err){
            res.status(401).json({
                error: err 
            })
        } else {
            res.status(201).json({
                message: 'Success!'
            })
        }
    })
})

app.delete('/vetvisits', (req, res, next) => {
    let strAnimalID = req.body.animalid
    let strQuery = 'DELETE FROM tblVetVisits WHERE AnimalID = ?'
    db.all(strQuery, [strAnimalID], (err) => {
        if(err){
            res.status(404).json({
                error: err
            })
        } else {
            res.status(200).json({
                message: 'Success!'
            }) 
        }
    })
})

// http://localhost:8000/animals
// http://localhost:8000/feeding
// http://localhost:8000/vetvisits
// http://localhost:8000/app.html