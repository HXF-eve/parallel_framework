package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// Relay2SubContract contract for handling IoTDatas
type Relay2SubContract struct {
	contractapi.Contract
}

//toChaincodeArgs generates args for chaincode invoke
func toChaincodeArgs(args ...string) [][]byte {
	bargs := make([][]byte, len(args))
	for i, arg := range args {
		bargs[i] = []byte(arg)
	}
	return bargs
}


func (cc *Relay2SubContract) RetrievePKData(ctx CustomTransactionContextInterface, id string, newid string) error {
	
	queryArgs := toChaincodeArgs("GetPKData", id)
	response := ctx.GetStub().InvokeChaincode("relayGeneralCC", queryArgs, "relay-channe")

	if response.Status != 200 {
		errors.New("InvokeChaincode return " + response.Message)
	}

	if response.Payload == nil {
		return errors.New("InvokeChaincode returns nil!")
	}


	data := new(PKData)
	
	err := json.Unmarshal(response.Payload, data)

	if err != nil {
		return fmt.Errorf("Data retrieved from world state for key %s was not of type IoTData", id)
	}
	
	
	newID := newid
	writeArgs := toChaincodeArgs("NewPKData", newID, data.Payload)
	response = ctx.GetStub().InvokeChaincode("subGeneralCC", writeArgs, "sub-channel")

	if response.Status != 200 {
		errors.New("InvokeChaincode return " + response.Message)
	}

	return nil
}

// func (cc *Relay2SubContract) RetrieveAllData(ctx CustomTransactionContextInterface, from string, readCC string) error {

// 	queryArgs := toChaincodeArgs("GetAllData")
// 	response := ctx.GetStub().InvokeChaincode(readCC, queryArgs, from)
	
// 	if response.Status != 200 {
// 		errors.New("InvokeChaincode return " + response.Message)
// 	}

// 	payload := string(response.Payload)
// 	if payload == nil {
// 		return errors.New("InvokeChaincode return nil!")
// 	}
// 	// // var payloads []string
// 	// // for raw := range dataList{
// 	// // 	rawBytes, _ := json.Marshal(raw)
// 	// // 	payloads = append(payloads, performHash(rawBytes))
// 	// // }

// 	// payload := strings.Join(payloads, "")

// 	data := new(UploadData)
// 	data.From = from
// 	data.Payload = payload
// 	data.SetDataUnread()
// 	dataBytes, _ := json.Marshal(data)
// 	newID := from + ":All"

// 	err := ctx.GetStub().PutState(newID, []byte(dataBytes))

// 	if err != nil {
// 		return errors.New("Unable to interact with world state")
// 	}

// 	return nil
// }