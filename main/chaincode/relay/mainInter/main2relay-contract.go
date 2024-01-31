package main

import (
	"encoding/json"
	"errors"
	"fmt"
	// "strings"
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// Main2RelayContract contract for handling IoTDatas
type Main2RelayContract struct {
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


func (cc *Main2RelayContract) UploadPKData(ctx CustomTransactionContextInterface, id string, newid string) error {
	
	queryArgs := toChaincodeArgs("GetPKData", id)
	response := ctx.GetStub().InvokeChaincode("mainGeneralCC", queryArgs, "main-channel")

	if response.Status != 200 {
		errors.New("InvokeChaincode return " + response.Message)
	}
	if response.Payload == nil {
		return errors.New("InvokeChaincode returns nil!")
	}

	data := new(PKData)
	err := json.Unmarshal(response.Payload, data)

	if err != nil {
		return fmt.Errorf("Data retrieved from world state for key %s was not of type PKData", id)
	}

	writeArgs := toChaincodeArgs("UploadPKData", newid, data.Payload)
	response = ctx.GetStub().InvokeChaincode("relayGeneralCC", writeArgs, "relay-channel")

	if response.Status != 200 {
		errors.New("InvokeChaincode return " + response.Message)
	}


	return nil
}



